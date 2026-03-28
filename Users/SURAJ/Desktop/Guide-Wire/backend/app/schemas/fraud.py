from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class FraudAnalyzeRequest(BaseModel):
    worker_id: int
    policy_id: int
    expected_income: float = Field(..., gt=0)
    actual_income: float = Field(..., ge=0)
    lat: float
    lon: float
    zone: str = "central"
    activity_score: float = Field(..., ge=0.0, le=1.0)
    request_hour: Optional[int] = Field(None, ge=0, le=23)


class FraudAnalyzeResponse(BaseModel):
    request_id: str
    worker_id: int
    policy_id: int

    # Composite result
    fraud_score: float
    decision: str
    decision_confidence: str
    decision_message: str

    # Sub-component audit trail
    anomaly_detection: dict[str, Any]
    location_check: dict[str, Any]
    activity_validation: dict[str, Any]
    duplicate_check: dict[str, Any]

    # Meta
    weights: dict[str, float]
    timestamp: str
