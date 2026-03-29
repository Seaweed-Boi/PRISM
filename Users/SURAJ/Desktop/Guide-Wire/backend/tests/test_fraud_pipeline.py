import pytest
from unittest.mock import patch
from app.ml.fraud_pipeline import run_fraud_pipeline, _location_check, _activity_check, _decision

def test_location_check_valid():
    # central zone is 12.90 to 13.05, 77.55 to 77.65
    res = _location_check(12.97, 77.59, "central")
    assert res["in_zone"] is True
    assert res["sub_score"] == 0.05
    assert res["result"] == "in_zone"

def test_location_check_invalid():
    res = _location_check(14.00, 78.00, "central")
    assert res["in_zone"] is False
    assert res["sub_score"] == 0.70
    assert res["result"] == "out_of_zone"

def test_location_check_spoofed():
    # latitude greater than 90 is physically impossible without spoofing/error
    res = _location_check(95.0, 77.0, "central")
    assert res["in_zone"] is False
    assert res["sub_score"] == 1.0
    assert res["result"] == "invalid_coordinates"

def test_activity_check():
    assert _activity_check(0.8)["level"] == "active"
    assert _activity_check(0.8)["sub_score"] == 0.05
    
    assert _activity_check(0.5)["level"] == "moderate"
    assert _activity_check(0.5)["sub_score"] == 0.35
    
    assert _activity_check(0.25)["level"] == "low"
    assert _activity_check(0.25)["sub_score"] == 0.60
    
    assert _activity_check(0.01)["level"] == "inactive"
    assert _activity_check(0.01)["sub_score"] == 0.90
    
    # Invalid score -> automatic high risk
    assert _activity_check(1.5)["result"] == "invalid_activity_score"
    assert _activity_check(1.5)["sub_score"] == 0.90

def test_decision():
    assert _decision(0.15)["decision"] == "approve"
    assert _decision(0.15)["confidence"] == "high"

    assert _decision(0.40)["decision"] == "approve"
    assert _decision(0.40)["confidence"] == "medium"

    assert _decision(0.60)["decision"] == "review"

    assert _decision(0.80)["decision"] == "reject"

@patch("app.ml.fraud_pipeline._fraud_svc")
@patch("app.ml.anomaly_detector.AnomalyDetector.score")
def test_fraud_pipeline_approve(mock_anomaly, mock_fraud_svc):
    # Mock anomaly detection to return a low score
    mock_anomaly.return_value = {
        "income_deviation_score": 0.1,
        "temporal_score": 0.05,
        "pattern_score": 0.0,
        "anomaly_score": 0.1,
    }
    # Mock redis duplicate check to return unique
    mock_fraud_svc.duplicate_score.return_value = 0.0

    res = run_fraud_pipeline(
        worker_id=1,
        policy_id=1,
        expected_income=220,
        actual_income=70,
        lat=12.97,
        lon=77.59,
        zone="central",
        activity_score=0.82,
        request_hour=14,
    )

    # Weights: anomaly 0.3, loc 0.25, act 0.25, dup 0.2
    # sub scores: anomaly=0.1, loc=0.05, act=0.05, dup=0.0
    # Composite = 0.3*0.1 + 0.25*0.05 + 0.25*0.05 + 0.2*0.0 = 0.03 + 0.0125 + 0.0125 = 0.055
    assert res.fraud_score == 0.055
    assert res.decision["decision"] == "approve"

@patch("app.ml.fraud_pipeline._fraud_svc")
@patch("app.ml.anomaly_detector.AnomalyDetector.score")
def test_fraud_pipeline_reject(mock_anomaly, mock_fraud_svc):
    # Simulate a highly suspicious claim
    mock_anomaly.return_value = {
        "income_deviation_score": 0.9,
        "temporal_score": 0.8,
        "pattern_score": 0.9,
        "anomaly_score": 0.9,
    }
    mock_fraud_svc.duplicate_score.return_value = 0.95

    res = run_fraud_pipeline(
        worker_id=1,
        policy_id=1,
        expected_income=220,
        actual_income=200, # Not a huge drop but suspicious patterns
        lat=0.0, # out of zone
        lon=0.0,
        zone="central",
        activity_score=0.05, # inactive
        request_hour=3, 
    )

    # Weights: anomaly 0.3, loc 0.25, act 0.25, dup 0.2
    # sub scores: anomaly=0.9, loc=0.70, act=0.90, dup=0.95
    # Composite = 0.27 + 0.175 + 0.225 + 0.19 = 0.86
    assert res.fraud_score == 0.86
    assert res.decision["decision"] == "reject"

# ══════════════════════════════════════════════════════════════════════════
# NEW — Dataset Generator Tests
# ══════════════════════════════════════════════════════════════════════════

import os
import pandas as pd

class TestDatasetGenerator:

    def test_generate_returns_dataframe(self, tmp_path):
        from app.ml.generate_dataset import generate
        out = str(tmp_path / "test_claims.csv")
        df = generate(n_samples=200, fraud_rate=0.18, output_path=out)
        assert isinstance(df, pd.DataFrame)

    def test_dataset_has_correct_columns(self, tmp_path):
        from app.ml.generate_dataset import generate
        out = str(tmp_path / "test_claims.csv")
        df = generate(n_samples=200, fraud_rate=0.18, output_path=out)
        required = [
            "worker_id", "policy_id", "zone",
            "expected_income", "actual_income", "income_delta",
            "delta_ratio", "gps_offset_m", "disruption_score",
            "activity_score", "claim_hour", "is_duplicate",
            "fraud_signals", "is_fraud",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_dataset_row_count(self, tmp_path):
        from app.ml.generate_dataset import generate
        out = str(tmp_path / "test_claims.csv")
        df = generate(n_samples=500, fraud_rate=0.18, output_path=out)
        assert len(df) == 500

    def test_fraud_label_is_binary(self, tmp_path):
        from app.ml.generate_dataset import generate
        out = str(tmp_path / "test_claims.csv")
        df = generate(n_samples=200, fraud_rate=0.18, output_path=out)
        assert set(df["is_fraud"].unique()).issubset({0, 1})

    def test_feature_ranges_are_valid(self, tmp_path):
        from app.ml.generate_dataset import generate
        out = str(tmp_path / "test_claims.csv")
        df = generate(n_samples=500, fraud_rate=0.18, output_path=out)
        assert df["gps_offset_m"].min() >= 0
        assert df["disruption_score"].between(0, 1).all()
        assert df["activity_score"].between(0, 1).all()
        assert df["claim_hour"].between(0, 23).all()
        assert df["expected_income"].gt(0).all()

    def test_labelling_rule_two_signals_is_fraud(self):
        from app.ml.generate_dataset import _label
        result = _label(
            gps=6000,         # signal 1 — out of zone
            dis=0.10,         # signal 2 — no real disruption
            act=0.80,
            hour=14,
            delta_ratio=0.50,
            is_dup=False,
        )
        assert result == 1

    def test_labelling_rule_one_signal_is_legit(self):
        from app.ml.generate_dataset import _label
        result = _label(
            gps=6000,         # signal 1 only
            dis=0.60,         # ok
            act=0.80,         # ok
            hour=14,          # ok
            delta_ratio=0.50, # ok
            is_dup=False,
        )
        assert result == 0


# ══════════════════════════════════════════════════════════════════════════
# NEW — ML Model Tests
# ══════════════════════════════════════════════════════════════════════════

import pytest
class TestMLModel:

    @pytest.fixture(scope="class")
    def trained_bundle(self, tmp_path_factory):
        from app.ml.generate_dataset import generate
        from app.ml.train_model import load_data, train_random_forest, save_model, load_model
        import pickle

        tmp = tmp_path_factory.mktemp("ml_test")
        data_path  = str(tmp / "claims.csv")
        model_path = str(tmp / "model.pkl")
        report_path = str(tmp / "report.txt")

        # Step 1 — generate small dataset
        generate(n_samples=800, fraud_rate=0.18, output_path=data_path)

        # Step 2 — load data and train directly (no path juggling)
        from sklearn.model_selection import train_test_split
        X, y, le = load_data(data_path)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )
        model = train_random_forest(X_train, y_train)

        # Step 3 — save to temp path directly
        from app.ml.train_model import FEATURE_COLS
        import pandas as pd
        bundle = {
            "model":         model,
            "label_encoder": le,
            "feature_cols":  FEATURE_COLS,
            "version":       "1.0.0",
            "trained_on":    pd.Timestamp.now().isoformat(),
        }
        with open(model_path, "wb") as f:
            pickle.dump(bundle, f)

        # Step 4 — load and return
        return load_model(model_path)

    def test_bundle_has_required_keys(self, trained_bundle):
        assert "model"         in trained_bundle
        assert "label_encoder" in trained_bundle
        assert "feature_cols"  in trained_bundle

    def test_score_returns_float_in_range(self, trained_bundle):
        from app.ml.train_model import ml_fraud_score
        score = ml_fraud_score(
            trained_bundle,
            gps_offset_m=200, disruption_score=0.75,
            activity_score=0.85, claim_hour=14,
            delta_ratio=0.55, income_delta=110.0,
            is_duplicate=0, zone="central",
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_legit_claim_scores_low(self, trained_bundle):
        from app.ml.train_model import ml_fraud_score
        score = ml_fraud_score(
            trained_bundle,
            gps_offset_m=150,
            disruption_score=0.80,
            activity_score=0.90,
            claim_hour=14,
            delta_ratio=0.55,
            income_delta=110.0,
            is_duplicate=0,
            zone="central",
        )
        assert score < 0.4, f"Legit claim scored too high: {score}"

    def test_fraud_claim_scores_high(self, trained_bundle):
        from app.ml.train_model import ml_fraud_score
        score = ml_fraud_score(
            trained_bundle,
            gps_offset_m=12000,
            disruption_score=0.05,
            activity_score=0.02,
            claim_hour=3,
            delta_ratio=0.97,
            income_delta=180.0,
            is_duplicate=1,
            zone="unknown",
        )
        assert score > 0.5, f"Fraud claim scored too low: {score}"

    def test_unknown_zone_does_not_crash(self, trained_bundle):
        from app.ml.train_model import ml_fraud_score
        score = ml_fraud_score(
            trained_bundle,
            gps_offset_m=300, disruption_score=0.6,
            activity_score=0.7, claim_hour=11,
            delta_ratio=0.45, income_delta=90.0,
            is_duplicate=0, zone="mars",
        )
        assert 0.0 <= score <= 1.0
