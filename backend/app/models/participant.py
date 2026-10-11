"""Participant database model."""

import uuid
from datetime import datetime, date, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.trial import Trial


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("trial_id", "participant_id", name="uq_trial_participant_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trial_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    visits_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    visits_planned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enrollment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_visit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_visit_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    trial: Mapped["Trial"] = relationship("Trial", back_populates="participants")

    def __repr__(self) -> str:
        return f"<Participant id={self.id} code={self.participant_id} status={self.status}>"
