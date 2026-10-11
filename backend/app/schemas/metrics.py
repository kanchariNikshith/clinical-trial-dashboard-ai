"""Schemas for trial metric responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class MetricDataQuality(BaseModel):
    status_counts_reconcile: bool
    warning: str | None = None
    unsupported_statuses: list[str] = Field(default_factory=list)


class StatusBreakdownItem(BaseModel):
    status: str
    label: str
    count: int
    rate: float
    summary: str


class TrialMetricsResponse(BaseModel):
    trial_id: str
    total_participants: int
    completed_count: int
    withdrawn_count: int
    active_count: int
    completion_rate: float
    withdrawal_rate: float
    active_rate: float
    calculation_method: str = "backend"
    empty_trial: bool = False
    ai_generated: bool = False
    data_quality: MetricDataQuality
    definitions: dict[str, str]
    status_breakdown: list[StatusBreakdownItem]
    summary: str

    model_config = ConfigDict(extra="allow")
