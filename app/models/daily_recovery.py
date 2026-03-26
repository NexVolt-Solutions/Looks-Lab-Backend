from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DailyRecovery(Base):
    __tablename__ = "daily_recovery"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_recovery_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sleep: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stretched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    