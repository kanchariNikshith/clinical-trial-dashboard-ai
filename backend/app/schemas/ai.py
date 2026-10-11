"""Pydantic schemas for aggregate-only AI insight requests and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AIInsightTopic(str, Enum):
    ENROLLMENT = "enrollment"
    COMPLETION = "completion"
    WITHDRAWALS = "withdrawals"
    PARTICIPANT_STATUS_DISTRIBUTION = "participant_status_distribution"


class AIAnalysisRequest(BaseModel):
    topic: AIInsightTopic = Field(
        ...,
        description="Allowed operational topic for the AI summary. The backend maps this to a fixed prompt.",
    )

    model_config = ConfigDict(extra="forbid")


class AIAnalysisResponse(BaseModel):
    analysis: str = Field(..., min_length=1, description="Plain-text AI-generated operational summary")
    model: str = Field(..., description="Provider model identifier used for generation")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="UTC timestamp for when the AI result was produced",
    )
    disclaimer: str = Field(
        default="AI-generated operational summary; review independently. Not a clinical conclusion.",
        description="Required human-review advisory text",
    )

    model_config = ConfigDict(from_attributes=True)
