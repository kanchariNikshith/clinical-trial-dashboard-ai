"""Authentication service implementing user registration, verification, and audit trail."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.schemas.user import UserRegisterRequest
from backend.app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    normalize_email,
)
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
