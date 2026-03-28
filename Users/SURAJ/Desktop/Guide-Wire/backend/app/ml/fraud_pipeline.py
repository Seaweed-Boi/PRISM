"""
PRISM Fraud Detection Engine — Full Pipeline

Architecture (matching reference image):

  User App
    ↓
  Cloudflare (Security Layer)          ← handled by middleware/cloudflare_security.py
    ↓
  Fraud Detection Engine
    ├── Anomaly Detection (ML)         ← ml/anomaly_detector.py
    ├── Location Check (GPS)           ← this module
    ├── Activity Validation            ← this module
    └── Duplicate Check (Redis)        ← fraud_service.py (duplicate_score)
    ↓
  Fraud Score                          ← weighted composite
    ↓
  Decision Engine                      ← approve / review / reject

All sub-components return a sub_score (0..1) and a detail dict so the
API can present a transparent, auditable pipeline trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.ml.anomaly_detector import AnomalyDetector
from app.services.fraud_service import FraudService


# ── Known valid delivery zones (lat_min, lat_max, lon_min, lon_max) ────────
_ZONE_BOUNDS: dict[str, tuple[float, float, float, float]] = {
    "north":   (28.60, 28.80, 77.10, 77.30),
    "south":   (12.85, 13.05, 77.55, 77.75),
    "east":    (22.55, 22.65, 88.30, 88.45),
    "west":    (19.00, 19.20, 72.80, 73.00),
    "central": (12.90, 13.05, 77.55, 77.65),
    # fallback – any valid globe co-ordinate is accepted
    "unknown": (-90.0, 90.0, -180.0, 180.0),
}

_FRAUD_SCORE_WEIGHTS = {
    "anomaly":    0.30,
    "location":   0.25,
    "activity":   0.25,
    "duplicate":  0.20,
}

_fraud_svc = FraudService()


# ── Sub-component: GPS Location Check ─────────────────────────────────────

def _location_check(lat: float, lon: float, zone: str) -> dict:
    """
    Validates that the GPS co-ordinates fall inside the expected delivery zone.
    Returns sub_score (0 = clean, 1 = spoofed/out-of-zone) and details.
    """
    if abs(lat) > 90 or abs(lon) > 180:
        return {"sub_score": 1.0, "result": "invalid_coordinates", "in_zone": False}

    bounds = _ZONE_BOUNDS.get(zone.lower(), _ZONE_BOUNDS["unknown"])
    lat_min, lat_max, lon_min, lon_max = bounds
    in_zone = lat_min <= lat <= lat_max and lon_min <= lon <= lon_max

    sub_score = 0.05 if in_zone else 0.70
    return {
        "sub_score": sub_score,
        "result": "in_zone" if in_zone else "out_of_zone",
        "in_zone": in_zone,
        "expected_bounds": {"lat": [lat_min, lat_max], "lon": [lon_min, lon_max]},
    }


# ── Sub-component: Activity Validation ────────────────────────────────────

def _activity_check(activity_score: float) -> dict:
    """
    Validates worker activity level at the time of the claim.
    A very low activity score during a claim window is suspicious.
    """
    if activity_score < 0.0 or activity_score > 1.0:
        return {"sub_score": 0.9, "result": "invalid_activity_score"}

    if activity_score >= 0.7:
        return {"sub_score": 0.05, "result": "high_activity", "level": "active"}
    if activity_score >= 0.4:
        return {"sub_score": 0.35, "result": "moderate_activity", "level": "moderate"}
    if activity_score >= 0.2:
        return {"sub_score": 0.60, "result": "low_activity", "level": "low"}
    return {"sub_score": 0.90, "result": "inactive", "level": "inactive"}


# ── Sub-component: Duplicate Check (Redis) ────────────────────────────────

def _duplicate_check(worker_id: int, policy_id: int, expected: float, actual: float) -> dict:
    score = _fraud_svc.duplicate_score(worker_id, policy_id, expected, actual)
    return {
        "sub_score": score,
        "result": "duplicate_detected" if score >= 0.9 else "unique_claim",
        "is_duplicate": score >= 0.9,
    }


# ── Decision Engine ───────────────────────────────────────────────────────

def _decision(fraud_score: float) -> dict:
    """
    Maps composite fraud_score to a decision with recommendation.
    """
    if fraud_score < 0.30:
        return {"decision": "approve", "confidence": "high",
                "message": "Low fraud risk. Auto-approve and initiate payout."}
    if fraud_score < 0.55:
        return {"decision": "approve", "confidence": "medium",
                "message": "Moderate risk indicators. Approve with enhanced monitoring."}
    if fraud_score < 0.75:
        return {"decision": "review", "confidence": "low",
                "message": "Elevated fraud signals detected. Flag for manual review."}
    return {"decision": "reject", "confidence": "high",
            "message": "High fraud probability. Claim rejected automatically."}


# ── Public API ────────────────────────────────────────────────────────────

@dataclass
class FraudPipelineResult:
    worker_id: int
    policy_id: int
    request_id: str

    # Sub-component results
    anomaly: dict
    location: dict
    activity: dict
    duplicate: dict

    # Aggregate
    fraud_score: float
    decision: dict

    # Audit
    timestamp: str
    weights: dict


def run_fraud_pipeline(
    *,
    worker_id: int,
    policy_id: int,
    expected_income: float,
    actual_income: float,
    lat: float,
    lon: float,
    zone: str,
    activity_score: float,
    request_hour: Optional[int] = None,
    request_id: str = "unknown",
) -> FraudPipelineResult:
    """
    Executes the full fraud detection pipeline and returns a structured result
    with per-component sub-scores, the composite fraud_score, and the
    decision engine verdict.
    """
    now = datetime.now(timezone.utc)
    if request_hour is None:
        request_hour = now.hour

    anomaly = AnomalyDetector.score(worker_id, actual_income, expected_income, request_hour)
    location = _location_check(lat, lon, zone)
    activity = _activity_check(activity_score)
    duplicate = _duplicate_check(worker_id, policy_id, expected_income, actual_income)

    sub_scores = {
        "anomaly":   anomaly["anomaly_score"],
        "location":  location["sub_score"],
        "activity":  activity["sub_score"],
        "duplicate": duplicate["sub_score"],
    }

    fraud_score = round(
        sum(sub_scores[k] * _FRAUD_SCORE_WEIGHTS[k] for k in sub_scores),
        3,
    )

    decision = _decision(fraud_score)

    return FraudPipelineResult(
        worker_id=worker_id,
        policy_id=policy_id,
        request_id=request_id,
        anomaly=anomaly,
        location=location,
        activity=activity,
        duplicate=duplicate,
        fraud_score=fraud_score,
        decision=decision,
        timestamp=now.isoformat(),
        weights=_FRAUD_SCORE_WEIGHTS,
    )
