"""Pydantic schemas for CSV preview and import responses."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ParticipantPreviewRow(BaseModel):
    participant_id: str
    status: str
    visits_completed: Optional[int] = None
    visits_planned: Optional[int] = None
    enrollment_date: Optional[str] = None
    last_visit_date: Optional[str] = None
    next_visit_due_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ParticipantPreviewResponse(BaseModel):
    total_rows: int = Field(description="Total data rows seen in the CSV")
    valid_rows: int = Field(description="Rows that passed validation without issue")
    invalid_rows: int = Field(description="Rows rejected by validation")
    errors: list[str] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list)


class ParticipantImportResponse(BaseModel):
    trial_id: str
    imported_count: int
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[str] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list)
