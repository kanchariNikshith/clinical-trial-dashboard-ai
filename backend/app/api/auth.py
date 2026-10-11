"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.models.user import User
from backend.app.services.auth_service import (
    register_user,
    authenticate_user,
    issue_refresh_session,
    rotate_refresh_session,
    revoke_user_refresh_tokens,
)
from backend.app.services.audit_service import (
    record_audit_event,
    ACTION_AUTH_LOGOUT,
)
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach the refresh token to a secure HTTP-only cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAME_SITE,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    request: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register an account with email and password, returning an access token."""
    user = register_user(db=db, request=request)
    token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = issue_refresh_session(db=db, user=user)
    set_refresh_cookie(response, refresh_token)
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
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user credentials and issue a signed access token."""
    user = authenticate_user(db=db, email=request.email, password=request.password)
    token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = issue_refresh_session(db=db, user=user)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh an expired access token")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Rotate the refresh token and issue a fresh access token for an active session."""
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session expired. Please sign in again.",
        )

    user, rotated_refresh_token = rotate_refresh_session(db=db, refresh_token=refresh_token_value)
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    set_refresh_cookie(response, rotated_refresh_token)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", summary="Logout current user")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Record logout audit event and revoke the refresh token for this user."""
    revoke_user_refresh_tokens(db=db, user_id=current_user.id)
    response.delete_cookie("refresh_token", path="/")
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
