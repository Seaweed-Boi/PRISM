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
