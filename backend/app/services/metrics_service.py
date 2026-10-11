"""Deterministic trial metrics service."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.participant import Participant
from backend.app.models.trial import Trial

SUPPORTED_STATUSES = ("completed", "withdrawn", "active")
STATUS_LABELS = {
    "completed": "Completed",
    "withdrawn": "Withdrawn",
    "active": "Active",
}


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _status_summary(label: str, count: int, rate: float) -> str:
    return f"{label}: {count} participants ({rate:.2f}%)"


def get_trial_metrics(db: Session, trial_id: str) -> dict[str, Any]:
    """Compute aggregate trial metrics using persisted participant rows."""
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TRIAL_NOT_FOUND",
                "message": f"Trial with id '{trial_id}' was not found.",
                "details": ["The requested trial could not be found or is not accessible."],
            },
        )

    participants = db.query(Participant).filter(Participant.trial_id == trial_id).all()
    counts = {status: 0 for status in SUPPORTED_STATUSES}
    unsupported_statuses: set[str] = set()

    for participant in participants:
        normalized = (participant.status or "").strip().lower()
        if normalized in counts:
            counts[normalized] += 1
        else:
            unsupported_statuses.add(normalized or "unknown")

    total_participants = len(participants)
    completed_count = counts["completed"]
    withdrawn_count = counts["withdrawn"]
    active_count = counts["active"]

    completion_rate = _safe_rate(completed_count, total_participants)
    withdrawal_rate = _safe_rate(withdrawn_count, total_participants)
    active_rate = _safe_rate(active_count, total_participants)

    if total_participants == 0:
        reconciled = True
        warning = None
        empty_trial = True
    else:
        reconciled = completed_count + withdrawn_count + active_count == total_participants and not unsupported_statuses
        empty_trial = False
        if reconciled:
            warning = None
        else:
            unsupported_note = (
                f" Unsupported statuses detected: {', '.join(sorted(unsupported_statuses))}."
                if unsupported_statuses
                else ""
            )
            warning = (
                "Data quality warning: participant status counts do not reconcile to the total "
                f"participants ({completed_count + withdrawn_count + active_count} of {total_participants})."
                f"{unsupported_note}"
            )

    status_breakdown = []
    for status in SUPPORTED_STATUSES:
        count = counts[status]
        rate = _safe_rate(count, total_participants)
        label = STATUS_LABELS[status]
        status_breakdown.append(
            {
                "status": status,
                "label": label,
                "count": count,
                "rate": rate,
                "summary": _status_summary(label, count, rate),
            }
        )

    if total_participants == 0:
        summary = "No participants available for this trial yet. Import a CSV to generate status metrics."
    else:
        summary = (
            f"{total_participants} participants: {completed_count} completed ({completion_rate:.2f}%), "
            f"{withdrawn_count} withdrawn ({withdrawal_rate:.2f}%), {active_count} active ({active_rate:.2f}%)."
        )

    return {
        "trial_id": trial_id,
        "total_participants": total_participants,
        "completed_count": completed_count,
        "withdrawn_count": withdrawn_count,
        "active_count": active_count,
        "completion_rate": completion_rate,
        "withdrawal_rate": withdrawal_rate,
        "active_rate": active_rate,
        "calculation_method": "backend",
        "empty_trial": empty_trial,
        "ai_generated": False,
        "data_quality": {
            "status_counts_reconcile": reconciled,
            "warning": warning,
            "unsupported_statuses": sorted(unsupported_statuses),
        },
        "definitions": {
            "total_participants": "count of imported participant records for the trial",
            "completed_count": "participants whose status is completed",
            "withdrawn_count": "participants whose status is withdrawn",
            "active_count": "participants whose status is active",
            "completion_rate": "completed_count / total_participants * 100",
            "withdrawal_rate": "withdrawn_count / total_participants * 100",
            "active_rate": "active_count / total_participants * 100",
        },
        "status_breakdown": status_breakdown,
        "summary": summary,
    }
