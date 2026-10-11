"""Trial management API endpoints."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.trial import Trial
from backend.app.models.user import User
from backend.app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from backend.app.schemas.metrics import TrialMetricsResponse
from backend.app.schemas.participant import (
    ParticipantImportResponse,
    ParticipantPreviewResponse,
)
from backend.app.schemas.trial import (
    TrialCreate,
    TrialUpdate,
    TrialResponse,
    TrialListResponse,
)
from backend.app.services import gemini_service
from backend.app.services.audit_service import ACTION_AI_ANALYSIS, record_audit_event
from backend.app.services.metrics_service import get_trial_metrics
from backend.app.services.participant_service import import_participants, preview_participants
from backend.app.services import dataset_service
from backend.app.services.trial_service import (
    create_trial,
    list_trials,
    get_trial,
    update_trial,
)
from backend.app.api.deps import get_current_user, require_trial_ownership

router = APIRouter(prefix="/trials", tags=["Trials"])


@router.post(
    "",
    response_model=TrialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new clinical trial",
)
def create_trial_endpoint(
    payload: TrialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrialResponse:
    """
    Create a new trial owned by the authenticated user.

    - Trial codes must be unique per user (HTTP 409 on duplicate).
    - Status must be one of: active, paused, completed, cancelled.
    - end_date must not precede start_date.
    """
    trial = create_trial(db=db, owner=current_user, payload=payload)
    return TrialResponse.from_orm_with_count(trial)


@router.get(
    "",
    response_model=TrialListResponse,
    summary="List all trials owned by the current user",
)
def list_trials_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrialListResponse:
    """Return all trials belonging to the authenticated user, newest first."""
    trials = list_trials(db=db, owner=current_user)
    trial_responses = [TrialResponse.from_orm_with_count(t) for t in trials]
    return TrialListResponse(trials=trial_responses, total=len(trial_responses))


@router.get(
    "/{trial_id}",
    response_model=TrialResponse,
    summary="Get a single trial by ID",
)
def get_trial_endpoint(
    trial_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrialResponse:
    """
    Retrieve a trial by its UUID.

    Returns HTTP 404 if not found; HTTP 403 if owned by another user.
    """
    trial = get_trial(db=db, trial_id=trial_id, owner=current_user)
    return TrialResponse.from_orm_with_count(trial)


@router.patch(
    "/{trial_id}",
    response_model=TrialResponse,
    summary="Partially update a trial",
)
def update_trial_endpoint(
    trial_id: str,
    payload: TrialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrialResponse:
    """
    Update any subset of trial fields.

    Returns HTTP 404/403 if trial not found or not owned by user.
    Returns HTTP 409 on trial_code collision.
    """
    trial = update_trial(db=db, trial_id=trial_id, owner=current_user, payload=payload)
    return TrialResponse.from_orm_with_count(trial)


@router.get(
    "/{trial_id}/metrics",
    response_model=TrialMetricsResponse,
    summary="Return deterministic trial metrics and data-quality diagnostics",
)
def get_trial_metrics_endpoint(
    trial_id: str,
    current_user: User = Depends(get_current_user),
    trial: Trial = Depends(require_trial_ownership),
    db: Session = Depends(get_db),
) -> TrialMetricsResponse:
    """Return aggregated participant metrics for a trial. The calculation is backend-generated only."""
    metrics = get_trial_metrics(db=db, trial_id=trial_id)
    return TrialMetricsResponse(**metrics)


@router.post(
    "/{trial_id}/ai-analysis",
    response_model=AIAnalysisResponse,
    summary="Generate an aggregate-only AI summary for a trial",
)
async def generate_trial_ai_analysis_endpoint(
    trial_id: str,
    payload: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    trial: Trial = Depends(require_trial_ownership),
    db: Session = Depends(get_db),
) -> AIAnalysisResponse:
    """Generate a short advisory AI summary using only aggregate metrics and a sanitized prompt."""
    metrics = get_trial_metrics(db=db, trial_id=trial_id)
    prompt = gemini_service.build_ai_prompt(metrics=metrics, topic=payload.topic)

    try:
        gemini_service.ensure_gemini_configured()
        result = await gemini_service.generate_ai_insight(prompt)
    except gemini_service.GeminiConfigurationError as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_SERVICE_UNAVAILABLE", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "AI_SERVICE_UNAVAILABLE",
                "message": "AI insight service is unavailable because the Gemini API key is not configured.",
                "details": ["Set GEMINI_API_KEY in the backend environment to enable AI insights."],
            },
        ) from exc
    except gemini_service.GeminiTimeoutError as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_SERVICE_TIMEOUT", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "code": "AI_SERVICE_TIMEOUT",
                "message": "The AI insight request hit a timeout while generating the summary.",
                "details": ["Please try again after a short delay."],
            },
        ) from exc
    except gemini_service.GeminiRateLimitError as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_RATE_LIMITED", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "AI_RATE_LIMITED",
                "message": "The AI service is temporarily rate-limited.",
                "details": ["Please retry the request shortly."],
            },
        ) from exc
    except gemini_service.GeminiProviderError as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_PROVIDER_ERROR", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": "The AI provider returned an invalid or unavailable response.",
                "details": ["Please try again in a moment."],
            },
        ) from exc
    except TimeoutError as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_SERVICE_TIMEOUT", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "code": "AI_SERVICE_TIMEOUT",
                "message": "The AI insight request hit a timeout while generating the summary.",
                "details": ["Please try again after a short delay."],
            },
        ) from exc
    except RuntimeError as exc:
        if "429" in str(exc) or "rate limit" in str(exc).lower() or "quota" in str(exc).lower():
            record_audit_event(
                db=db,
                action=ACTION_AI_ANALYSIS,
                entity_type="trial",
                outcome="error",
                actor_user_id=current_user.id,
                entity_id=trial_id,
                metadata={"error_code": "AI_RATE_LIMITED", "topic": payload.topic.value},
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "AI_RATE_LIMITED",
                    "message": "The AI service is temporarily rate-limited.",
                    "details": ["Please retry the request shortly."],
                },
            ) from exc
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_PROVIDER_ERROR", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": "The AI provider returned an invalid or unavailable response.",
                "details": ["Please try again in a moment."],
            },
        ) from exc
    except ValueError as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_PROVIDER_ERROR", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": "The AI provider returned an invalid response payload.",
                "details": ["The AI output could not be validated."],
            },
        ) from exc

    try:
        response = AIAnalysisResponse(**result)
    except Exception as exc:
        record_audit_event(
            db=db,
            action=ACTION_AI_ANALYSIS,
            entity_type="trial",
            outcome="error",
            actor_user_id=current_user.id,
            entity_id=trial_id,
            metadata={"error_code": "AI_RESPONSE_INVALID", "topic": payload.topic.value},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "AI_RESPONSE_INVALID",
                "message": "The AI provider returned an invalid response payload.",
                "details": ["The output could not be validated."],
            },
        ) from exc

    record_audit_event(
        db=db,
        action=ACTION_AI_ANALYSIS,
        entity_type="trial",
        outcome="success",
        actor_user_id=current_user.id,
        entity_id=trial_id,
        metadata={"model": response.model, "topic": payload.topic.value},
    )
    return response


@router.post(
    "/{trial_id}/participants/preview",
    response_model=ParticipantPreviewResponse,
    summary="Validate a CSV file and return a preview without saving participants",
)
async def preview_participants_endpoint(
    trial_id: str,
    file: UploadFile = File(...),
    trial: Trial = Depends(require_trial_ownership),
    db: Session = Depends(get_db),
) -> ParticipantPreviewResponse:
    """Preview a CSV upload for participant validation without writing to the database."""
    result = await preview_participants(file=file, db=db, trial_id=trial_id)
    return ParticipantPreviewResponse(
        total_rows=result["total_rows"],
        valid_rows=result["valid_rows"],
        invalid_rows=result["invalid_rows"],
        errors=result["errors"],
        preview=result["preview"],
    )


@router.post(
    "/{trial_id}/datasets/preview",
    summary="Profile an uploaded dataset CSV and detect dataset type without persisting",
)
async def preview_dataset_endpoint(
    trial_id: str,
    file: UploadFile = File(...),
    trial: Trial = Depends(require_trial_ownership),
    db: Session = Depends(get_db),
) -> dict:
    """Return a dataset profile and deterministic dataset-type classification.

    If the classifier detects a participant roster, the response will include the
    participant preview structure for backward compatibility. Other dataset types
    are profiled and classified but not persisted.
    """
    # Read bytes once and use independent in-memory file-like objects so
    # downstream services don't interfere by consuming the stream.
    if hasattr(file, "read"):
        content = await file.read()
    else:
        content = b""

    import io as _io

    profiling_file = type("F", (), {"filename": file.filename, "file": _io.BytesIO(content)})()
    profile = dataset_service.profile_csv(profiling_file)
    classification = dataset_service.classify_dataset(profile)

    response: dict = {"profile": profile, "classification": classification}

    # If participant roster, include participant preview details using existing service
    if classification.get("type") == "participant_roster":
        try:
            preview_file = type("F", (), {"filename": file.filename, "file": _io.BytesIO(content)})()
            preview = await preview_participants(file=preview_file, db=db, trial_id=trial_id)
            response["participant_preview"] = preview
        except Exception as exc:
            # If participant preview fails, include the error details but don't block the profile response.
            response["participant_preview"] = {"error": str(exc)}

    return response


@router.post(
    "/{trial_id}/participants/import",
    response_model=ParticipantImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate and import participants after explicit confirmation",
)
async def import_participants_endpoint(
    trial_id: str,
    file: UploadFile = File(...),
    confirm: bool = Form(False),
    trial: Trial = Depends(require_trial_ownership),
    db: Session = Depends(get_db),
) -> ParticipantImportResponse:
    """Import a CSV only after explicit confirmation and server-side validation has passed."""
    result = await import_participants(file=file, db=db, trial_id=trial_id, confirmed=confirm)
    return ParticipantImportResponse(
        trial_id=result["trial_id"],
        imported_count=result["imported_count"],
        total_rows=result["total_rows"],
        valid_rows=result["valid_rows"],
        invalid_rows=result["invalid_rows"],
        errors=result["errors"],
        preview=result["preview"],
    )
