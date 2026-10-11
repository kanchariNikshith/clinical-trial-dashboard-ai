"""Tests for Phase 4 metrics and status charts."""

import uuid

import pytest
from httpx import AsyncClient

from backend.app.models.participant import Participant


def _build_status_counts(total: int, *, completed: int, withdrawn: int, active: int) -> list[str]:
    statuses = ["completed"] * completed + ["withdrawn"] * withdrawn + ["active"] * active
    assert len(statuses) == total
    return statuses


@pytest.mark.asyncio
async def test_metrics_ac030_fixture_matches_expected_rates(async_client: AsyncClient, db_session) -> None:
    """Metrics are calculated deterministically and match the AC-030 fixture."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "metrics-ac030@example.com", "password": "Password123!"},
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers,
        json={
            "trial_code": "MET-030",
            "trial_name": "Status Metrics Fixture",
            "status": "active",
        },
    )
    assert trial.status_code == 201
    trial_id = trial.json()["id"]

    for index, status in enumerate(_build_status_counts(120, completed=95, withdrawn=15, active=10), start=1):
        db_session.add(
            Participant(
                trial_id=trial_id,
                participant_id=f"P-{index:03d}",
                status=status,
            )
        )
    db_session.commit()

    response = await async_client.get(f"/api/trials/{trial_id}/metrics", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["trial_id"] == trial_id
    assert payload["total_participants"] == 120
    assert payload["completed_count"] == 95
    assert payload["withdrawn_count"] == 15
    assert payload["active_count"] == 10
    assert payload["completion_rate"] == 79.17
    assert payload["withdrawal_rate"] == 12.5
    assert payload["active_rate"] == 8.33
    assert payload["data_quality"]["status_counts_reconcile"] is True
    assert payload["calculation_method"] == "backend"
    assert payload["summary"].startswith("120 participants")
    assert "95 completed" in payload["summary"]


@pytest.mark.asyncio
async def test_metrics_are_backend_computed_not_ai_generated(async_client: AsyncClient, db_session) -> None:
    """The metrics payload must declare a backend computation source and not AI generation."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "metrics-source@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers,
        json={"trial_code": "MET-SRC", "trial_name": "Backend Source", "status": "active"},
    )
    trial_id = trial.json()["id"]

    db_session.add_all(
        [
            Participant(trial_id=trial_id, participant_id="P-001", status="completed"),
            Participant(trial_id=trial_id, participant_id="P-002", status="withdrawn"),
            Participant(trial_id=trial_id, participant_id="P-003", status="active"),
        ]
    )
    db_session.commit()

    response = await async_client.get(f"/api/trials/{trial_id}/metrics", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["calculation_method"] == "backend"
    assert payload.get("ai_generated") is not True
    assert payload["definitions"]["completion_rate"].startswith("completed_count")


@pytest.mark.asyncio
async def test_zero_participant_trial_returns_safe_empty_state(async_client: AsyncClient) -> None:
    """Empty trials should not divide by zero and should expose a clear empty-state summary."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "metrics-empty@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers,
        json={"trial_code": "MET-EMPTY", "trial_name": "Empty Trial", "status": "active"},
    )
    trial_id = trial.json()["id"]

    response = await async_client.get(f"/api/trials/{trial_id}/metrics", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["total_participants"] == 0
    assert payload["completed_count"] == 0
    assert payload["withdrawn_count"] == 0
    assert payload["active_count"] == 0
    assert payload["completion_rate"] == 0.0
    assert payload["withdrawal_rate"] == 0.0
    assert payload["active_rate"] == 0.0
    assert payload["empty_trial"] is True
    assert "no participants" in payload["summary"].lower()


@pytest.mark.asyncio
async def test_inconsistent_status_counts_raise_data_quality_warning(async_client: AsyncClient, db_session) -> None:
    """Unsupported or mismatched status totals should trigger a data-quality warning."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "metrics-warning@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers,
        json={"trial_code": "MET-WARN", "trial_name": "Warning Trial", "status": "active"},
    )
    trial_id = trial.json()["id"]

    db_session.add_all(
        [
            Participant(trial_id=trial_id, participant_id="P-001", status="completed"),
            Participant(trial_id=trial_id, participant_id="P-002", status="active"),
            Participant(trial_id=trial_id, participant_id="P-003", status="paused"),
        ]
    )
    db_session.commit()

    response = await async_client.get(f"/api/trials/{trial_id}/metrics", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["data_quality"]["status_counts_reconcile"] is False
    assert "warning" in payload["data_quality"]["warning"].lower()


@pytest.mark.asyncio
async def test_metrics_endpoint_requires_authentication_and_ownership(async_client: AsyncClient) -> None:
    """The metrics endpoint must require auth and enforce trial ownership."""
    reg_a = await async_client.post(
        "/api/auth/register",
        json={"email": "ownera@example.com", "password": "Password123!"},
    )
    reg_b = await async_client.post(
        "/api/auth/register",
        json={"email": "ownerb@example.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers_a,
        json={"trial_code": "MET-OWN", "trial_name": "Private Trial", "status": "active"},
    )
    trial_id = trial.json()["id"]

    unauth = await async_client.get(f"/api/trials/{trial_id}/metrics")
    assert unauth.status_code == 401

    forbidden = await async_client.get(f"/api/trials/{trial_id}/metrics", headers=headers_b)
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_metrics_endpoint_rejects_missing_or_invalid_trial_ids(async_client: AsyncClient) -> None:
    """Missing and invalid trial IDs should return proper 404 errors."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "metrics-invalid@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    missing = await async_client.get(f"/api/trials/{uuid.uuid4()}/metrics", headers=headers)
    assert missing.status_code == 404
    assert "not found" in missing.json()["error"]["message"].lower()

    invalid = await async_client.get("/api/trials/not-a-uuid/metrics", headers=headers)
    assert invalid.status_code == 404


@pytest.mark.asyncio
async def test_metrics_status_breakdown_includes_human_readable_labels(async_client: AsyncClient, db_session) -> None:
    """The breakdown should include readable labels and descriptions suitable for UI display."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "metrics-labels@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers,
        json={"trial_code": "MET-LABELS", "trial_name": "Labels Trial", "status": "active"},
    )
    trial_id = trial.json()["id"]

    db_session.add_all(
        [
            Participant(trial_id=trial_id, participant_id="P-001", status="completed"),
            Participant(trial_id=trial_id, participant_id="P-002", status="completed"),
            Participant(trial_id=trial_id, participant_id="P-003", status="withdrawn"),
            Participant(trial_id=trial_id, participant_id="P-004", status="active"),
        ]
    )
    db_session.commit()

    response = await async_client.get(f"/api/trials/{trial_id}/metrics", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    labels = [item["label"] for item in payload["status_breakdown"]]
    assert "Completed" in labels
    assert "Withdrawn" in labels
    assert "Active" in labels
    assert any("Completed" in item["summary"] for item in payload["status_breakdown"])
    assert any("Active" in item["summary"] for item in payload["status_breakdown"])
