"""
/api/v1/fraud — Fraud Detection Engine endpoints

Exposes the full PRISM fraud pipeline as seen in the architecture diagram:

  User App → Cloudflare → Fraud Detection Engine → Fraud Score → Decision Engine

POST /api/v1/fraud/analyze
  Run the full pipeline and return a detailed audit trace (no DB write).

GET  /api/v1/fraud/pipeline-status
  Returns the architecture components and their live status.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter

from app.schemas.fraud import FraudAnalyzeRequest, FraudAnalyzeResponse
from app.ml.fraud_pipeline import run_fraud_pipeline

router = APIRouter()


@router.post("/analyze", response_model=FraudAnalyzeResponse)
def analyze_fraud(payload: FraudAnalyzeRequest):
    """
    Runs the full fraud detection pipeline without writing a claim.
    Useful for previewing risk before submitting a claim, or for demo purposes.
    """
    request_id = str(uuid4())
    result = run_fraud_pipeline(
        worker_id=payload.worker_id,
        policy_id=payload.policy_id,
        expected_income=payload.expected_income,
        actual_income=payload.actual_income,
        lat=payload.lat,
        lon=payload.lon,
        zone=payload.zone,
        activity_score=payload.activity_score,
        request_hour=payload.request_hour,
        request_id=request_id,
    )

    return FraudAnalyzeResponse(
        request_id=result.request_id,
        worker_id=result.worker_id,
        policy_id=result.policy_id,
        fraud_score=result.fraud_score,
        decision=result.decision["decision"],
        decision_confidence=result.decision["confidence"],
        decision_message=result.decision["message"],
        anomaly_detection=result.anomaly,
        location_check=result.location,
        activity_validation=result.activity,
        duplicate_check=result.duplicate,
        weights=result.weights,
        timestamp=result.timestamp,
    )


@router.get("/pipeline-status")
def pipeline_status():
    """
    Returns the current architecture component status for the pipeline diagram.
    All components are always available (anomaly detector and location check are
    in-process; Redis duplicate check degrades gracefully to 0.0 when offline).
    """
    from app.services.fraud_service import FraudService
    fs = FraudService()
    redis_ok = fs._redis is not None

    return {
        "pipeline": [
            {
                "layer": "Security",
                "component": "Cloudflare Security Middleware",
                "status": "active",
                "description": "Rate limiting, bot scoring, country blocking, CF-Ray validation",
            },
            {
                "layer": "Fraud Detection",
                "component": "Anomaly Detection (ML)",
                "status": "active",
                "description": "Statistical income deviation, temporal pattern, repeat-value detection",
            },
            {
                "layer": "Fraud Detection",
                "component": "Location Check (GPS)",
                "status": "active",
                "description": "Validates GPS co-ordinates against known delivery zone bounding boxes",
            },
            {
                "layer": "Fraud Detection",
                "component": "Activity Validation",
                "status": "active",
                "description": "Worker activity score threshold validation",
            },
            {
                "layer": "Fraud Detection",
                "component": "Duplicate Check (Redis)",
                "status": "active" if redis_ok else "degraded",
                "description": "SHA-1 claim fingerprint dedup via Redis; falls back to 0 score when Redis is offline",
            },
            {
                "layer": "Scoring",
                "component": "Fraud Score Aggregator",
                "status": "active",
                "description": "Weighted composite: anomaly×0.30 + location×0.25 + activity×0.25 + duplicate×0.20",
            },
            {
                "layer": "Decision",
                "component": "Decision Engine",
                "status": "active",
                "description": "Thresholds: <0.30 approve, 0.30–0.55 approve+monitor, 0.55–0.75 review, ≥0.75 reject",
            },
        ]
    }
