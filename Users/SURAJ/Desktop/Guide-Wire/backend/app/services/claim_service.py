from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.fraud_audit import FraudAudit
from app.services.payout_service import PayoutService
from app.ml.fraud_pipeline import FraudPipelineResult


class ClaimService:
    @staticmethod
    def evaluate_and_process(
        db: Session,
        worker_id: int,
        policy_id: int,
        expected_income: float,
        actual_income: float,
        trigger_source: str,
        fraud_result: FraudPipelineResult,
    ) -> tuple[Claim, bool, float]:
        loss = max(expected_income - actual_income, 0)
        
        # Map pipeline decision to claim status
        decision_str = fraud_result.decision.get("decision", "review").lower()
        if decision_str == "approve" and loss > 0:
            status = "approved"
        elif decision_str == "review":
            status = "pending"
        else:
            status = "rejected"

        claim = Claim(
            worker_id=worker_id,
            policy_id=policy_id,
            trigger_source=trigger_source,
            expected_income=expected_income,
            actual_income=actual_income,
            loss_amount=loss,
            fraud_score=fraud_result.fraud_score,
            status=status,
        )
        db.add(claim)
        db.commit()
        db.refresh(claim)

        # Create FraudAudit record
        audit = FraudAudit(
            claim_id=claim.id,
            worker_id=worker_id,
            policy_id=policy_id,
            fraud_score=fraud_result.fraud_score,
            decision=fraud_result.decision.get("decision", "unknown"),
            decision_confidence=fraud_result.decision.get("confidence", "unknown"),
            decision_message=fraud_result.decision.get("message", ""),
            anomaly_detection_data=fraud_result.anomaly,
            location_check_data=fraud_result.location,
            activity_validation_data=fraud_result.activity,
            duplicate_check_data=fraud_result.duplicate,
            weights_data=fraud_result.weights,
        )
        db.add(audit)
        db.commit()

        payout_amount = 0.0
        payout_done = False
        if status == "approved":
            payout_amount = round(loss * 0.9, 2)
            PayoutService.process(db, claim.id, worker_id, payout_amount)
            payout_done = True

        return claim, payout_done, payout_amount
