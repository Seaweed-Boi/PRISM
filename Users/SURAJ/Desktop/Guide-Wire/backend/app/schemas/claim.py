from datetime import datetime
from pydantic import BaseModel


class ClaimTrigger(BaseModel):
    worker_id: int
    policy_id: int
    expected_income: float
    actual_income: float
    trigger_source: str
    lat: float
    lon: float
    activity_score: float


class ClaimOut(BaseModel):
    id: int
    worker_id: int
    policy_id: int
    trigger_source: str
    expected_income: float
    actual_income: float
    loss_amount: float
    fraud_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
