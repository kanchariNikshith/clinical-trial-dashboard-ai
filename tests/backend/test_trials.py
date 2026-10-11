"""Tests for Phase 2 trial management behavior (AC-010, AC-011, AC-012)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_list_and_update_trial(async_client: AsyncClient) -> None:
    """An authenticated owner can create, list, and update their own trial."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "phase2_owner@trialops.org", "password": "Password123!"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = await async_client.post(
        "/api/trials",
        headers=headers,
        json={
            "trial_code": "TRIAL-001",
            "trial_name": "Synthetic Trial Demo",
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
    )
    assert create.status_code == 201
    payload = create.json()
    assert payload["trial_code"] == "TRIAL-001"
    assert payload["participant_count"] == 0

    list_response = await async_client.get("/api/trials", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = await async_client.get(f"/api/trials/{payload['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["trial_name"] == "Synthetic Trial Demo"

    update_response = await async_client.patch(
        f"/api/trials/{payload['id']}",
        headers=headers,
        json={"status": "paused", "end_date": "2026-11-30"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "paused"


@pytest.mark.asyncio
async def test_trial_duplicate_code_and_invalid_dates_are_rejected(async_client: AsyncClient) -> None:
    """Duplicate trial codes and invalid date ranges are rejected with clear API errors."""
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": "phase2_duplicate@trialops.org", "password": "Password123!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    first = await async_client.post(
        "/api/trials",
        headers=headers,
        json={
            "trial_code": "DUP-001",
            "trial_name": "First Trial",
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": None,
        },
    )
    assert first.status_code == 201

    duplicate = await async_client.post(
        "/api/trials",
        headers=headers,
        json={
            "trial_code": "DUP-001",
            "trial_name": "Conflicting Trial",
            "status": "active",
            "start_date": "2026-01-02",
            "end_date": None,
        },
    )
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["error"]["message"].lower()

    invalid = await async_client.post(
        "/api/trials",
        headers=headers,
        json={
            "trial_code": "DUP-002",
            "trial_name": "Bad Dates",
            "status": "active",
            "start_date": "2026-08-10",
            "end_date": "2026-08-01",
        },
    )
    assert invalid.status_code == 422
    assert "end_date cannot precede start_date" in invalid.json()["error"]["message"]


@pytest.mark.asyncio
async def test_trial_isolation_across_users(async_client: AsyncClient) -> None:
    """One user cannot read or modify another user's trial."""
    user_a = await async_client.post(
        "/api/auth/register",
        json={"email": "trial_owner_a@trialops.org", "password": "Password123!"},
    )
    user_b = await async_client.post(
        "/api/auth/register",
        json={"email": "trial_owner_b@trialops.org", "password": "Password123!"},
    )

    a_headers = {"Authorization": f"Bearer {user_a.json()['access_token']}"}
    b_headers = {"Authorization": f"Bearer {user_b.json()['access_token']}"}

    created = await async_client.post(
        "/api/trials",
        headers=a_headers,
        json={"trial_code": "OWNER-A-01", "trial_name": "Private Trial", "status": "active"},
    )
    trial_id = created.json()["id"]

    forbidden_get = await async_client.get(f"/api/trials/{trial_id}", headers=b_headers)
    assert forbidden_get.status_code == 403

    forbidden_patch = await async_client.patch(
        f"/api/trials/{trial_id}",
        headers=b_headers,
        json={"trial_name": "Changed by intruder"},
    )
    assert forbidden_patch.status_code == 403
