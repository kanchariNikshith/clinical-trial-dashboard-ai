"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.models.user import User
from backend.app.services.auth_service import register_user, authenticate_user
from backend.app.services.audit_service import (
    record_audit_event,
    ACTION_AUTH_LOGOUT,
)
from backend.app.core.security import create_access_token
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register an account with email and password, returning an access token."""
    user = register_user(db=db, request=request)
    token = create_access_token(data={"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT token",
)
def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user credentials and issue a signed access token."""
    user = authenticate_user(db=db, email=request.email, password=request.password)
    token = create_access_token(data={"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", summary="Logout current user")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Record logout audit event and instruct client to discard bearer token."""
    record_audit_event(
        db=db,
        action=ACTION_AUTH_LOGOUT,
        entity_type="user",
        entity_id=current_user.id,
        actor_user_id=current_user.id,
        outcome="success",
        metadata={"email": current_user.email},
    )
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse, summary="Get current authenticated user profile")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile for the currently signed-in user."""
    return UserResponse.model_validate(current_user)
