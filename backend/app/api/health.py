"""Health check endpoint."""

from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return application liveness status without exposing sensitive configuration."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.APP_ENV,
    )
