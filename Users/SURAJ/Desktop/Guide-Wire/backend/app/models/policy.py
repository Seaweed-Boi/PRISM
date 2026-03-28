from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"), index=True)
    week_start: Mapped[str] = mapped_column(String(20), nullable=False)
    week_end: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    premium: Mapped[float] = mapped_column(Float, nullable=False)
    expected_hourly_income: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
