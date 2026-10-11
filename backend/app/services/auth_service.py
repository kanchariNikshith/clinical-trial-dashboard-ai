"""Authentication service implementing user registration, verification, and audit trail."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import (
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    validate_password_strength,
    normalize_email,
)
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User
from backend.app.schemas.user import UserRegisterRequest
from backend.app.services.audit_service import (
    record_audit_event,
    ACTION_AUTH_REGISTER,
    ACTION_AUTH_LOGIN,
    ACTION_AUTH_LOGIN_FAILED,
)


def register_user(db: Session, request: UserRegisterRequest) -> User:
    """Register a new user with password validation and conflict handling."""
    normalized = normalize_email(request.email)

    # Validate password complexity
    password_error = validate_password_strength(request.password)
    if password_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error,
        )

    # Check for existing email
    existing_user = db.query(User).filter(User.email == normalized).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    hashed_pw = hash_password(request.password)
    user = User(
        email=normalized,
        password_hash=hashed_pw,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Record registration audit event
    record_audit_event(
        db=db,
        action=ACTION_AUTH_REGISTER,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        outcome="success",
        metadata={"email": normalized},
    )

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate user credentials.
    Returns User if valid; raises generic 401 on failure to avoid account enumeration.
    """
    normalized = normalize_email(email)
    user = db.query(User).filter(User.email == normalized).first()

    # Constant time / secure comparison
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        record_audit_event(
            db=db,
            action=ACTION_AUTH_LOGIN_FAILED,
            entity_type="user",
            outcome="failure",
            actor_user_id=user.id if user else None,
            metadata={"attempted_email": normalized},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record successful login audit event
    record_audit_event(
        db=db,
        action=ACTION_AUTH_LOGIN,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        outcome="success",
        metadata={"email": normalized},
    )

    return user


def issue_refresh_session(db: Session, user: User) -> str:
    """Issue a new refresh token for a user and return the raw token value."""
    now = datetime.now(timezone.utc)
    refresh_value = generate_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_value),
        family_id=str(uuid.uuid4()),
        created_at=now,
        expires_at=now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        last_used_at=now,
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_value


def _normalize_dt(value: datetime | None) -> datetime | None:
    """Normalize SQLite-returned naive timestamps to UTC-aware values for comparisons."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def rotate_refresh_session(db: Session, refresh_token: str) -> Tuple[User, str]:
    """Validate and rotate the refresh token, returning the user and the new raw refresh token."""
    now = datetime.now(timezone.utc)
    token_hash = hash_refresh_token(refresh_token)
    existing = (
        db.query(RefreshToken)
        .with_for_update()
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh session.",
        )

    revoked_at = _normalize_dt(existing.revoked_at)
    expires_at = _normalize_dt(existing.expires_at)
    if revoked_at or expires_at is None or expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh session.",
        )

    user = db.query(User).filter(User.id == existing.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is no longer active.",
        )

    new_refresh_value = generate_refresh_token()
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_refresh_value),
        family_id=existing.family_id,
        created_at=now,
        expires_at=now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        last_used_at=now,
    )
    db.add(new_token)
    db.flush()

    family_tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user.id,
            RefreshToken.family_id == existing.family_id,
        )
        .all()
    )

    for token in family_tokens:
        if token.revoked_at is not None:
            continue
        token.revoked_at = now
        token.last_used_at = now
        token.replaced_by_token_id = new_token.id

    existing.revoked_at = now
    existing.last_used_at = now
    existing.replaced_by_token_id = new_token.id

    db.commit()
    db.refresh(new_token)
    return user, new_refresh_value


def revoke_user_refresh_tokens(db: Session, user_id: str) -> None:
    """Invalidate all active refresh tokens for a user."""
    tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    for token in tokens:
        if token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
    db.commit()
