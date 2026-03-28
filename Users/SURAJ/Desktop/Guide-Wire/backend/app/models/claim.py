from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"), index=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), index=True)
    trigger_source: Mapped[str] = mapped_column(String(60), nullable=False)
    expected_income: Mapped[float] = mapped_column(Float, nullable=False)
    actual_income: Mapped[float] = mapped_column(Float, nullable=False)
    loss_amount: Mapped[float] = mapped_column(Float, nullable=False)
    fraud_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
