from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.worker import Worker
from app.models.policy import Policy
from app.models.claim import Claim
from app.models.payout import Payout
from app.schemas.dashboard import WorkerDashboard, AdminDashboard
from app.services.external_data_service import ExternalDataService

router = APIRouter()


@router.get("/worker/{worker_id}", response_model=WorkerDashboard)
def worker_dashboard(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    latest_policy = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id)
        .order_by(Policy.id.desc())
        .first()
    )
    total_payout = db.query(func.coalesce(func.sum(Payout.amount), 0)).filter(Payout.worker_id == worker_id).scalar() or 0
    active_policies = db.query(func.count(Policy.id)).filter(Policy.worker_id == worker_id, Policy.status == "active").scalar() or 0

    expected = latest_policy.expected_hourly_income if latest_policy else 0.0
    protected = round(expected * 8 * 6, 2)

    return WorkerDashboard(
        worker_id=worker_id,
        expected_hourly_income=expected,
        protected_income=protected,
        active_policies=active_policies,
        total_payout=round(total_payout, 2),
    )


@router.get("/admin", response_model=AdminDashboard)
def admin_dashboard(db: Session = Depends(get_db)):
    claims_total = db.query(func.count(Claim.id)).scalar() or 0
    claims_approved = db.query(func.count(Claim.id)).filter(Claim.status == "approved").scalar() or 0
    claims_rejected = db.query(func.count(Claim.id)).filter(Claim.status == "rejected").scalar() or 0

    low = db.query(func.count(Policy.id)).filter(Policy.risk_tier == "low").scalar() or 0
    medium = db.query(func.count(Policy.id)).filter(Policy.risk_tier == "medium").scalar() or 0
    high = db.query(func.count(Policy.id)).filter(Policy.risk_tier == "high").scalar() or 0

    zones = ["north", "south", "east", "west", "central"]
    heatmap = {}
    forecast = {}
    for zone in zones:
        snapshot = ExternalDataService.disruption_snapshot(zone)
        heatmap[zone] = round((snapshot["rainfall_mm"] / 140 + snapshot["congestion_index"] + snapshot["aqi"] / 500) / 3, 2)
        forecast[zone] = round(0.3 + heatmap[zone] * 0.7, 2)

    return AdminDashboard(
        disruption_heatmap=heatmap,
        risk_distribution={"low": low, "medium": medium, "high": high},
        claim_stats={"total": claims_total, "approved": claims_approved, "rejected": claims_rejected},
        weekly_risk_forecast=forecast,
    )
