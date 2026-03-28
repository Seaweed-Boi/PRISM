from datetime import datetime
from sqlalchemy.orm import Session

from app.models.payout import Payout


class PayoutService:
    @staticmethod
    def process(db: Session, claim_id: int, worker_id: int, amount: float) -> Payout:
        gateway_ref = f"SIM-UPI-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        payout = Payout(
            claim_id=claim_id,
            worker_id=worker_id,
            amount=round(amount, 2),
            gateway_ref=gateway_ref,
            status="processed",
        )
        db.add(payout)
        db.commit()
        db.refresh(payout)
        return payout
