"""Trial database model."""

import uuid
from datetime import datetime, date, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.participant import Participant


class Trial(Base):
    __tablename__ = "trials"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "trial_code", name="uq_owner_trial_code"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trial_code: Mapped[str] = mapped_column(String(100), nullable=False)
    trial_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
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

    owner: Mapped["User"] = relationship("User", back_populates="trials")
    participants: Mapped[List["Participant"]] = relationship(
        "Participant", back_populates="trial", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Trial id={self.id} code={self.trial_code} owner={self.owner_user_id}>"
