from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.worker import Worker
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyOut
from app.services.monitoring_service import MonitoringService
from app.services.risk_service import RiskService

router = APIRouter()


@router.post("", response_model=PolicyOut)
def buy_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == payload.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    expected_income, snapshot = MonitoringService.expected_hourly_income(worker.zone)
    risk_tier, premium = RiskService.compute_risk_tier(snapshot)

    policy = Policy(
        worker_id=payload.worker_id,
        week_start=payload.week_start,
        week_end=payload.week_end,
        risk_tier=risk_tier,
        premium=premium,
        expected_hourly_income=expected_income,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy
