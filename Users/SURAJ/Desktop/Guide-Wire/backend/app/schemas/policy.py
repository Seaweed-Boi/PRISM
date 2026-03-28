from datetime import datetime
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    worker_id: int
    week_start: str
    week_end: str


class PolicyOut(BaseModel):
    id: int
    worker_id: int
    week_start: str
    week_end: str
    risk_tier: str
    premium: float
    expected_hourly_income: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
