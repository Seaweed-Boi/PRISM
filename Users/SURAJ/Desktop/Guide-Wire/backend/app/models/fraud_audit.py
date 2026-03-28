from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FraudAudit(Base):
    __tablename__ = "fraud_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), index=True, nullable=True) # Optional in case it's a pre-check
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"), index=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), index=True)
    
    fraud_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_message: Mapped[str] = mapped_column(String(255), nullable=False)

    anomaly_detection_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    location_check_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    activity_validation_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    duplicate_check_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    weights_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
