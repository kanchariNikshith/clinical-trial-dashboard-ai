"""Trial management service — create, list, retrieve with ownership enforcement."""

from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.trial import Trial
from backend.app.models.user import User
from backend.app.schemas.trial import TrialCreate, TrialUpdate
from backend.app.services.audit_service import record_audit_event, ACTION_TRIAL_CREATE

# Allowed status values – enforced both on create and update.
ALLOWED_STATUSES = {"active", "completed", "paused", "cancelled"}


def _validate_status(status_value: str) -> None:
    """Raise HTTP 422 if the status is not in the allowed set."""
    if status_value not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid trial status '{status_value}'. "
                f"Allowed values: {sorted(ALLOWED_STATUSES)}."
            ),
        )


def _validate_dates(start_date: Optional[date], end_date: Optional[date]) -> None:
    """Raise HTTP 422 if end_date precedes start_date."""
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date cannot precede start_date.",
        )


def _validate_trial_code(trial_code: str) -> None:
    """Raise HTTP 422 if trial code contains invalid characters or is blank."""
    stripped = trial_code.strip()
    if not stripped:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="trial_code must not be blank or whitespace only.",
        )


def create_trial(db: Session, owner: User, payload: TrialCreate) -> Trial:
    """
    Create a new trial owned by the given user.

    Raises:
        HTTP 422 on invalid status, date range, or blank trial_code.
        HTTP 409 if the same user already has a trial with the same trial_code.
    """
    _validate_trial_code(payload.trial_code)
    _validate_status(payload.status)
    _validate_dates(payload.start_date, payload.end_date)

    # Duplicate check: (owner_user_id, trial_code) must be unique per user.
    existing = (
        db.query(Trial)
        .filter(
            Trial.owner_user_id == owner.id,
            Trial.trial_code == payload.trial_code.strip(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Trial code '{payload.trial_code}' already exists for this account. "
                "Trial codes must be unique per user."
            ),
        )

    trial = Trial(
        owner_user_id=owner.id,
        trial_code=payload.trial_code.strip(),
        trial_name=payload.trial_name.strip(),
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(trial)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Trial code '{payload.trial_code}' already exists for this account. "
                "Trial codes must be unique per user."
            ),
        )
    db.refresh(trial)

    record_audit_event(
        db=db,
        action=ACTION_TRIAL_CREATE,
        entity_type="trial",
        entity_id=trial.id,
        actor_user_id=owner.id,
        outcome="success",
        metadata={
            "trial_code": trial.trial_code,
            "trial_name": trial.trial_name,
            "status": trial.status,
        },
    )

    return trial


def list_trials(db: Session, owner: User) -> List[Trial]:
    """Return all trials owned by the authenticated user, newest first."""
    return (
        db.query(Trial)
        .filter(Trial.owner_user_id == owner.id)
        .order_by(Trial.created_at.desc())
        .all()
    )


def get_trial(db: Session, trial_id: str, owner: User) -> Trial:
    """
    Retrieve a single trial by ID, enforcing ownership.

    Raises:
        HTTP 404 if not found.
        HTTP 403 if owned by a different user.
    """
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trial '{trial_id}' was not found.",
        )
    if trial.owner_user_id != owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this trial.",
        )
    return trial


def update_trial(db: Session, trial_id: str, owner: User, payload: TrialUpdate) -> Trial:
    """
    Partially update a trial. Enforces ownership.

    Raises:
        HTTP 404/403 via get_trial.
        HTTP 422 on invalid status or date range.
        HTTP 409 on trial_code conflict with another of the user's trials.
    """
    trial = get_trial(db=db, trial_id=trial_id, owner=owner)

    if payload.status is not None:
        _validate_status(payload.status)

    new_start = payload.start_date if payload.start_date is not None else trial.start_date
    new_end = payload.end_date if payload.end_date is not None else trial.end_date
    _validate_dates(new_start, new_end)

    if payload.trial_code is not None:
        new_code = payload.trial_code.strip()
        _validate_trial_code(new_code)
        if new_code != trial.trial_code:
            conflict = (
                db.query(Trial)
                .filter(
                    Trial.owner_user_id == owner.id,
                    Trial.trial_code == new_code,
                    Trial.id != trial_id,
                )
                .first()
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Trial code '{new_code}' already exists for this account."
                    ),
                )
        trial.trial_code = new_code

    if payload.trial_name is not None:
        trial.trial_name = payload.trial_name.strip()
    if payload.status is not None:
        trial.status = payload.status
    if payload.start_date is not None:
        trial.start_date = payload.start_date
    if payload.end_date is not None:
        trial.end_date = payload.end_date

    db.commit()
    db.refresh(trial)
    return trial
