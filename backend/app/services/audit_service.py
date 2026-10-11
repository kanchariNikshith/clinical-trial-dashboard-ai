"""Audit logging service with non-sensitive allowlist sanitization."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.audit_event import AuditEvent

# Controlled actions
ACTION_AUTH_REGISTER = "auth.register"
ACTION_AUTH_LOGIN = "auth.login"
ACTION_AUTH_LOGIN_FAILED = "auth.login_failed"
ACTION_AUTH_LOGOUT = "auth.logout"
ACTION_TRIAL_CREATE = "trial.create"
ACTION_CSV_IMPORT = "csv.import"
ACTION_AI_ANALYSIS = "ai.analysis"
ACTION_REPORT_EXPORT = "report.export"

# Forbidden metadata keys that must never be recorded
FORBIDDEN_KEYS = {
    "password",
    "password_hash",
    "access_token",
    "token",
    "jwt",
    "secret",
    "api_key",
    "raw_rows",
    "participant_rows",
    "prompt",
}


def sanitize_metadata(meta: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Sanitize metadata by omitting any forbidden, secret, or row-level keys."""
    if not meta:
        return None
    cleaned: Dict[str, Any] = {}
    for k, v in meta.items():
        if k.lower() in FORBIDDEN_KEYS:
            continue
        # Truncate strings if too long
        if isinstance(v, str) and len(v) > 255:
            cleaned[k] = v[:255] + "..."
        elif isinstance(v, (int, float, bool, str, list, dict)):
            cleaned[k] = v
    return cleaned


def record_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    outcome: str,
    actor_user_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Record an audit event without logging passwords, tokens, or raw participant rows."""
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        outcome=outcome,
        metadata_json=sanitize_metadata(metadata),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
