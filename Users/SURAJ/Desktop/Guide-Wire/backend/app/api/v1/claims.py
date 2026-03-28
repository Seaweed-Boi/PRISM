from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.policy import Policy
from app.models.worker import Worker
from app.schemas.claim import ClaimOut, ClaimTrigger
from app.services.claim_service import ClaimService
from app.ml.fraud_pipeline import run_fraud_pipeline

router = APIRouter()


@router.post("/trigger", response_model=ClaimOut)
def trigger_claim(payload: ClaimTrigger, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == payload.policy_id, Policy.worker_id == payload.worker_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    worker = db.query(Worker).filter(Worker.id == payload.worker_id).first()
    worker_zone = worker.zone if worker else "unknown"

    request_id = f"clm_{uuid4().hex[:8]}"

    # Run the comprehensive fraud detection pipeline
    fraud_result = run_fraud_pipeline(
        worker_id=payload.worker_id,
        policy_id=payload.policy_id,
        expected_income=payload.expected_income,
        actual_income=payload.actual_income,
        lat=payload.lat,
        lon=payload.lon,
        zone=worker_zone,
        activity_score=payload.activity_score,
        request_id=request_id,
    )

    claim, _, _ = ClaimService.evaluate_and_process(
        db=db,
        worker_id=payload.worker_id,
        policy_id=payload.policy_id,
        expected_income=payload.expected_income,
        actual_income=payload.actual_income,
        trigger_source=payload.trigger_source,
        fraud_result=fraud_result, # pass full pipeline result instead of just score
    )
    return claim
