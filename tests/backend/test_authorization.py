"""Tests for trial authorization and cross-user data isolation (AC-004)."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.trial import Trial
from backend.app.api.deps import require_trial_ownership


def test_cross_user_trial_isolation(db_session: Session) -> None:
    """AC-004: One user's trial cannot be read or accessed by another user."""
    # Create User A
    user_a = User(email="user_a@trialops.org", password_hash="hash_a", is_active=True)
    # Create User B
    user_b = User(email="user_b@trialops.org", password_hash="hash_b", is_active=True)
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # User A creates a trial
    trial_a = Trial(
        owner_user_id=user_a.id,
        trial_code="TRIAL-A",
        trial_name="User A Confidential Trial",
        status="active",
    )
    db_session.add(trial_a)
    db_session.commit()

    # 1. User A accesses their own trial -> SUCCESS
    accessed = require_trial_ownership(trial_id=trial_a.id, current_user=user_a, db=db_session)
    assert accessed.id == trial_a.id
    assert accessed.trial_code == "TRIAL-A"

    # 2. User B attempts to access User A's trial -> 403 FORBIDDEN
    with pytest.raises(HTTPException) as exc_info:
        require_trial_ownership(trial_id=trial_a.id, current_user=user_b, db=db_session)
    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()

    # 3. Accessing non-existent trial -> 404 NOT FOUND
    with pytest.raises(HTTPException) as exc_info:
        require_trial_ownership(trial_id="non_existent_uuid", current_user=user_a, db=db_session)
    assert exc_info.value.status_code == 404
