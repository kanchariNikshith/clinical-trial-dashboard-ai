"""Comprehensive test suite for Authentication and User Registration."""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.audit_event import AuditEvent
from backend.app.models.refresh_token import RefreshToken
from backend.app.core.config import Settings
from backend.app.core.security import create_access_token, generate_refresh_token, hash_refresh_token
from backend.app.services.auth_service import issue_refresh_session, rotate_refresh_session


def test_testing_settings_require_postgres() -> None:
    """Testing configuration must reject the SQLite fallback and require an explicit PostgreSQL URL."""
    with pytest.raises(ValueError, match="PostgreSQL|Postgres|TEST_DATABASE_URL"):
        Settings(APP_ENV="testing", TEST_DATABASE_URL="sqlite:///./test_clinical.db")


@pytest.mark.asyncio
async def test_refresh_session_rejects_reused_family_tokens(async_client: AsyncClient, db_session: Session) -> None:
    """A refresh token replay should invalidate the remaining active tokens from that rotation family."""
    user = User(email="family_user@trialops.org", password_hash="fakehash", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token_a = issue_refresh_session(db_session, user)
    original_family_id = (
        db_session.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_refresh_token(token_a))
        .one()
        .family_id
    )

    token_b = generate_refresh_token()
    db_session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(token_b),
            family_id=original_family_id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            last_used_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    rotate_refresh_session(db_session, token_a)

    with pytest.raises(Exception):
        rotate_refresh_session(db_session, token_b)


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient, db_session: Session) -> None:
    """AC-001 & AC-005: Valid user can register, receives JWT, password hashed securely."""
    payload = {
        "email": "researcher_1@trialops.org",
        "password": "SecurePassword123!",
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "researcher_1@trialops.org"

    # Verify database persistence & password hashing (AC-005)
    db_user = db_session.query(User).filter(User.email == "researcher_1@trialops.org").first()
    assert db_user is not None
    assert db_user.password_hash != "SecurePassword123!"
    assert db_user.password_hash.startswith("$2b$")  # bcrypt format

    # Verify audit event recorded without password
    event = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "auth.register", AuditEvent.entity_id == db_user.id)
        .first()
    )
    assert event is not None
    assert event.outcome == "success"
    assert "password" not in (event.metadata_json or {})


@pytest.mark.asyncio
async def test_register_weak_passwords(async_client: AsyncClient) -> None:
    """Verify password policy rejects weak passwords."""
    cases = [
        ("short1!", "Password must be at least 8 characters long."),
        ("nouppercase123!", "Password must contain at least one uppercase letter."),
        ("NOLOWERCASE123!", "Password must contain at least one lowercase letter."),
        ("NoDigitsOrSpecial", "Password must contain at least one digit or special character."),
    ]
    for pwd, expected_msg in cases:
        response = await async_client.post(
            "/api/auth/register",
            json={"email": f"test_{pwd[:5]}@trialops.org", "password": pwd},
        )
        assert response.status_code == 400 or response.status_code == 422
        assert expected_msg in response.text


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient) -> None:
    """Duplicate email registration is rejected with HTTP 409 conflict."""
    payload = {
        "email": "duplicate@trialops.org",
        "password": "ValidPassword123!",
    }
    res1 = await async_client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, db_session: Session) -> None:
    """AC-001: Authenticated user can log in and receives token."""
    # Register first
    await async_client.post(
        "/api/auth/register",
        json={"email": "login_user@trialops.org", "password": "Password123!"},
    )

    # Login
    response = await async_client.post(
        "/api/auth/login",
        json={"email": "login_user@trialops.org", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_user@trialops.org"

    # Verify audit event recorded
    event = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "auth.login", AuditEvent.outcome == "success")
        .first()
    )
    assert event is not None


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, db_session: Session) -> None:
    """AC-002: Invalid credentials return generic 401 without account enumeration."""
    # Register user
    await async_client.post(
        "/api/auth/register",
        json={"email": "auth_target@trialops.org", "password": "CorrectPassword123!"},
    )

    # Wrong password
    response = await async_client.post(
        "/api/auth/login",
        json={"email": "auth_target@trialops.org", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text

    # Verify failed audit event
    failed_event = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "auth.login_failed", AuditEvent.outcome == "failure")
        .first()
    )
    assert failed_event is not None


@pytest.mark.asyncio
async def test_login_nonexistent_account(async_client: AsyncClient) -> None:
    """AC-002: Non-existent account returns the same generic 401 message."""
    response = await async_client.post(
        "/api/auth/login",
        json={"email": "does_not_exist@trialops.org", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


@pytest.mark.asyncio
async def test_refresh_cookie_issues_new_access_token(async_client: AsyncClient) -> None:
    """A valid refresh cookie rotates the session without requiring a new login."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "refresh_user@trialops.org", "password": "Password123!"},
    )
    assert reg.status_code == 201

    login = await async_client.post(
        "/api/auth/login",
        json={"email": "refresh_user@trialops.org", "password": "Password123!"},
    )
    assert login.status_code == 200

    refresh_cookie = login.cookies.get("refresh_token")
    assert refresh_cookie, "login response did not include a refresh cookie"

    response = await async_client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "refresh_user@trialops.org"
    assert "refresh_token" in response.headers.get("set-cookie", "").lower()


@pytest.mark.asyncio
async def test_me_endpoint_with_valid_token(async_client: AsyncClient) -> None:
    """Verify GET /api/auth/me returns authenticated profile."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "profile_user@trialops.org", "password": "Password123!"},
    )
    token = reg.json()["access_token"]

    response = await async_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile_user@trialops.org"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_me_endpoint_unauthorized(async_client: AsyncClient) -> None:
    """AC-003: Protected route without authorization returns 401."""
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_invalid_token(async_client: AsyncClient) -> None:
    """Invalid token returns 401."""
    response = await async_client.get(
        "/api/auth/me", headers={"Authorization": "Bearer invalid_malformed_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.text


@pytest.mark.asyncio
async def test_me_endpoint_expired_token(async_client: AsyncClient, db_session: Session) -> None:
    """Expired token returns 401 with expired message."""
    user = User(
        email="expired_user@trialops.org",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create expired token
    expired_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=timedelta(seconds=-10),
    )

    response = await async_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "expired" in response.text


@pytest.mark.asyncio
async def test_logout_records_audit_event(async_client: AsyncClient, db_session: Session) -> None:
    """Verify logout records audit event."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "logout_user@trialops.org", "password": "Password123!"},
    )
    token = reg.json()["access_token"]

    response = await async_client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    event = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "auth.logout", AuditEvent.outcome == "success")
        .first()
    )
    assert event is not None
