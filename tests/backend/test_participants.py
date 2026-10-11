"""Tests for Phase 3 CSV preview and import behavior."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from backend.app.models.participant import Participant


async def create_user_and_trial(async_client: AsyncClient, email: str, trial_code: str = "TRIAL-001") -> tuple[dict[str, str], str]:
    reg = await async_client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await async_client.post(
        "/api/trials",
        headers=headers,
        json={
            "trial_code": trial_code,
            "trial_name": "Synthetic Trial Demo",
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
    )
    assert create.status_code == 201, create.text
    return headers, create.json()["id"]


@pytest.mark.asyncio
async def test_preview_valid_csv_returns_preview_without_writing_records(async_client: AsyncClient, db_session: Session) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_preview@trialops.org", "TRIAL-PREVIEW")
    csv_body = """participant_id,status,visits_completed,visits_planned,enrollment_date,last_visit_date,next_visit_due_date
SYN-001,completed,8,8,2026-01-02,2026-04-10,
SYN-002,active,3,8,2026-01-05,2026-03-20,2026-04-15
"""

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("participants.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total_rows"] == 2
    assert payload["valid_rows"] == 2
    assert payload["invalid_rows"] == 0
    assert len(payload["preview"]) == 2
    assert db_session.query(Participant).count() == 0


@pytest.mark.asyncio
async def test_confirmed_import_successfully_persists_participants(async_client: AsyncClient, db_session: Session) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_import@trialops.org", "TRIAL-IMPORT")
    csv_body = """participant_id,status,visits_completed,visits_planned,enrollment_date,last_visit_date,next_visit_due_date
SYN-001,completed,8,8,2026-01-02,2026-04-10,
SYN-002,active,3,8,2026-01-05,2026-03-20,2026-04-15
"""

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/import",
        headers=headers,
        data={"confirm": "true"},
        files={"file": ("participants.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["imported_count"] == 2
    assert payload["invalid_rows"] == 0
    assert db_session.query(Participant).count() == 2


@pytest.mark.asyncio
async def test_preview_rejects_missing_headers_and_malformed_csv(async_client: AsyncClient) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_headers@trialops.org", "TRIAL-HEADERS")
    csv_body = """participant_id,visits_completed
SYN-001,3
"""

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("bad.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 422
    assert "required columns" in response.json()["error"]["message"].lower()
    assert "participant_id" in "\n".join(response.json()["error"]["details"]).lower()

    malformed = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("malformed.csv", "participant_id,status\nSYN-001,active\nSYN-002\n", "text/csv")},
    )
    assert malformed.status_code == 200
    assert malformed.json()["invalid_rows"] >= 1


@pytest.mark.asyncio
async def test_preview_rejects_trial_level_csv_with_clear_participant_format_message(async_client: AsyncClient) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_study_csv@trialops.org", "TRIAL-STUDY")
    csv_body = """NCT Number,Title,Status,Phase,Study Type
NCT0001,COVID vaccine trial,Completed,Phase 3,Interventional
NCT0002,Masking study,Active,Phase 2,Interventional
"""

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("COVID clinical trials.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 422, response.text
    payload = response.json()["error"]
    message = payload["message"].lower()
    details = "\n".join(payload["details"]).lower()
    assert "participant import format" in message or "participant csv" in message
    assert "participant_id" in details
    assert "status" in details
    assert "trial-level study export" in details or "participant roster" in details


@pytest.mark.asyncio
async def test_preview_flags_unsupported_status_invalid_dates_and_negative_visits(async_client: AsyncClient) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_invalid@trialops.org", "TRIAL-INVALID")
    csv_body = """participant_id,status,visits_completed,visits_planned,enrollment_date,last_visit_date,next_visit_due_date
SYN-001,unknown,3,8,2026-01-01,2026-02-01,2026-02-10
SYN-002,active,-1,8,2026-99-99,2026-02-10,2026-02-20
SYN-003,completed,9,8,2026-01-05,2026-02-01,2026-02-05
"""

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("invalid.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["invalid_rows"] == 3
    joined = "\n".join(payload["errors"])
    assert "status" in joined.lower() or "date" in joined.lower() or "visit" in joined.lower()


@pytest.mark.asyncio
async def test_duplicate_participant_codes_are_rejected(async_client: AsyncClient) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_duplicates@trialops.org", "TRIAL-DUPS")
    csv_body = """participant_id,status,visits_completed,visits_planned,enrollment_date,last_visit_date,next_visit_due_date
SYN-001,active,2,8,2026-01-01,2026-01-15,2026-01-20
SYN-001,withdrawn,1,8,2026-01-02,2026-01-18,2026-01-30
"""

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("duplicate.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["invalid_rows"] == 2
    assert any("duplicate" in message.lower() for message in payload["errors"])


@pytest.mark.asyncio
async def test_oversized_and_excessive_row_counts_are_rejected(async_client: AsyncClient) -> None:
    headers, trial_id = await create_user_and_trial(async_client, "phase3_volume@trialops.org", "TRIAL-VOLUME")
    large_content = "participant_id,status,visits_completed,visits_planned,enrollment_date,last_visit_date,next_visit_due_date\n" + "\n".join(
        f"SYN-{idx},active,2,8,2026-01-{(idx % 28) + 1},2026-01-15,2026-01-20" for idx in range(1, 10001)
    ) + "\n"

    response = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=headers,
        files={"file": ("large.csv", large_content, "text/csv")},
    )

    assert response.status_code == 413 or response.status_code == 422


@pytest.mark.asyncio
async def test_preview_and_import_require_auth_and_owned_trial(async_client: AsyncClient) -> None:
    user_a = await async_client.post(
        "/api/auth/register",
        json={"email": "phase3_owner_a@trialops.org", "password": "Password123!"},
    )
    user_b = await async_client.post(
        "/api/auth/register",
        json={"email": "phase3_owner_b@trialops.org", "password": "Password123!"},
    )
    token_a = user_a.json()["access_token"]
    token_b = user_b.json()["access_token"]
    a_headers = {"Authorization": f"Bearer {token_a}"}
    b_headers = {"Authorization": f"Bearer {token_b}"}

    trial = await async_client.post(
        "/api/trials",
        headers=a_headers,
        json={"trial_code": "OWNER-ONLY-01", "trial_name": "Private Trial", "status": "active"},
    )
    trial_id = trial.json()["id"]

    csv_body = "participant_id,status\nSYN-001,active\n"

    unauth = await async_client.post(f"/api/trials/{trial_id}/participants/preview", files={"file": ("x.csv", csv_body, "text/csv")})
    assert unauth.status_code == 401

    forbidden = await async_client.post(
        f"/api/trials/{trial_id}/participants/preview",
        headers=b_headers,
        files={"file": ("x.csv", csv_body, "text/csv")},
    )
    assert forbidden.status_code == 403

    bad_import = await async_client.post(
        f"/api/trials/{trial_id}/participants/import",
        headers=b_headers,
        data={"confirm": "true"},
        files={"file": ("x.csv", csv_body, "text/csv")},
    )
    assert bad_import.status_code == 403
