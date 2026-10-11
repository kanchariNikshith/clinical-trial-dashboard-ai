"""Tests for audit log sanitization and security policies (AC-060, AC-061)."""

from sqlalchemy.orm import Session
from backend.app.services.audit_service import (
    record_audit_event,
    sanitize_metadata,
    ACTION_AUTH_LOGIN,
)
from backend.app.models.audit_event import AuditEvent


def test_audit_metadata_sanitization(db_session: Session) -> None:
    """AC-061: Audit logging strictly filters out passwords, tokens, API keys, and sensitive data."""
    sensitive_input = {
        "email": "doctor@hospital.org",
        "password": "SuperSecretPassword123!",
        "password_hash": "$2b$12$somehashhere",
        "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
        "api_key": "AIzaSyD-secret-key",
        "valid_metric": 42,
    }

    sanitized = sanitize_metadata(sensitive_input)
    assert sanitized is not None
    assert "password" not in sanitized
    assert "password_hash" not in sanitized
    assert "access_token" not in sanitized
    assert "api_key" not in sanitized
    assert sanitized["email"] == "doctor@hospital.org"
    assert sanitized["valid_metric"] == 42

    event = record_audit_event(
        db=db_session,
        action=ACTION_AUTH_LOGIN,
        entity_type="user",
        outcome="success",
        metadata=sensitive_input,
    )

    db_event = db_session.query(AuditEvent).filter(AuditEvent.id == event.id).first()
    assert db_event is not None
    assert "password" not in db_event.metadata_json
    assert "access_token" not in db_event.metadata_json
