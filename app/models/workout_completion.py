from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WorkoutCompletion(Base):
    __tablename__ = "workout_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_workout_completion_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed_indices: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    total_exercises: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    