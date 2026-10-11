"""Trial Pydantic schemas for create, update, and response."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class TrialCreate(BaseModel):
    trial_code: str = Field(min_length=1, max_length=100, description="Unique trial code per user")
    trial_name: str = Field(min_length=1, max_length=255, description="Official study title")
    status: str = Field(default="active", description="Operational status: active|paused|completed|cancelled")
    start_date: Optional[date] = Field(default=None, description="Trial initiation date")
    end_date: Optional[date] = Field(default=None, description="Trial completion / closure date")

    @model_validator(mode="after")
    def validate_dates(self) -> "TrialCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot precede start_date")
        return self


class TrialUpdate(BaseModel):
    """Partial update — all fields optional. Only supplied fields are modified."""
    trial_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    trial_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[str] = Field(default=None)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)


class TrialResponse(BaseModel):
    id: str
    owner_user_id: str
    trial_code: str
    trial_name: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    participant_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_count(cls, trial: object) -> "TrialResponse":
        """Build response including derived participant count from the ORM relationship."""
        obj = cls.model_validate(trial)
        # Access the participants relationship (eagerly loaded or lazy)
        participants = getattr(trial, "participants", [])
        obj.participant_count = len(participants) if participants is not None else 0
        return obj


class TrialListResponse(BaseModel):
    trials: List[TrialResponse]
    total: int
