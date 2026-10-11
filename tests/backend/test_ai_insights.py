"""Tests for the Phase 5 Gemini AI insights flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.app.models.participant import Participant


async def _create_user_and_trial(async_client: AsyncClient, email: str, trial_code: str) -> tuple[dict, str]:
    register = await async_client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert register.status_code == 201, register.text
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    trial = await async_client.post(
        "/api/trials",
        headers=headers,
        json={"trial_code": trial_code, "trial_name": "AI Trial", "status": "active"},
    )
    assert trial.status_code == 201, trial.text
    return headers, trial.json()["id"]


@pytest.mark.asyncio
async def test_ai_analysis_success_with_mocked_provider(async_client: AsyncClient, db_session) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-success@example.com", "AI-OK")
    db_session.add_all(
        [
            Participant(trial_id=trial_id, participant_id="P-001", status="completed"),
            Participant(trial_id=trial_id, participant_id="P-002", status="withdrawn"),
            Participant(trial_id=trial_id, participant_id="P-003", status="active"),
        ]
    )
    db_session.commit()

    mock_result = {"analysis": "AI-generated operational summary", "model": "gemini-2.5-flash", "generated_at": "2026-01-01T00:00:00Z"}

    with patch("backend.app.services.gemini_service.generate_ai_insight", new=AsyncMock(return_value=mock_result)):
        response = await async_client.post(
            f"/api/trials/{trial_id}/ai-analysis",
            headers=headers,
            json={"topic": "enrollment"},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["analysis"] == "AI-generated operational summary"
    assert payload["disclaimer"].startswith("AI-generated")
    assert payload["model"] == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_ai_analysis_requires_authentication(async_client: AsyncClient) -> None:
    _, trial_id = await _create_user_and_trial(async_client, "ai-auth@example.com", "AI-AUTH")

    response = await async_client.post(f"/api/trials/{trial_id}/ai-analysis", json={"topic": "enrollment"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_analysis_requires_trial_ownership(async_client: AsyncClient) -> None:
    headers_a, trial_id = await _create_user_and_trial(async_client, "user-a@example.com", "AI-OWN")
    register_b = await async_client.post(
        "/api/auth/register",
        json={"email": "user-b@example.com", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {register_b.json()['access_token']}"}

    response = await async_client.post(
        f"/api/trials/{trial_id}/ai-analysis",
        headers=headers_b,
        json={"topic": "enrollment"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ai_analysis_missing_config_returns_service_unavailable(async_client: AsyncClient, monkeypatch) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-missing@example.com", "AI-MISS")
    monkeypatch.setattr("backend.app.core.config.settings.GEMINI_API_KEY", "")

    response = await async_client.post(
        f"/api/trials/{trial_id}/ai-analysis",
        headers=headers,
        json={"topic": "enrollment"},
    )

    assert response.status_code == 503
    assert "unavailable" in response.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_ai_analysis_timeout_is_handled_safely(async_client: AsyncClient) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-timeout@example.com", "AI-TIMEOUT")

    with patch("backend.app.services.gemini_service.generate_ai_insight", new=AsyncMock(side_effect=TimeoutError("timed out"))):
        response = await async_client.post(
            f"/api/trials/{trial_id}/ai-analysis",
            headers=headers,
            json={"topic": "enrollment"},
        )

    assert response.status_code == 504
    assert "timeout" in response.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_ai_analysis_rate_limit_is_handled_safely(async_client: AsyncClient) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-ratelimit@example.com", "AI-RATE")

    with patch("backend.app.services.gemini_service.generate_ai_insight", new=AsyncMock(side_effect=RuntimeError("429 Too Many Requests"))):
        response = await async_client.post(
            f"/api/trials/{trial_id}/ai-analysis",
            headers=headers,
            json={"topic": "enrollment"},
        )

    assert response.status_code == 429
    assert "rate" in response.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_ai_analysis_malformed_provider_output_is_rejected(async_client: AsyncClient) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-malformed@example.com", "AI-MALFORMED")

    with patch("backend.app.services.gemini_service.generate_ai_insight", new=AsyncMock(return_value={"bad": "payload"})):
        response = await async_client.post(
            f"/api/trials/{trial_id}/ai-analysis",
            headers=headers,
            json={"topic": "enrollment"},
        )

    assert response.status_code == 502
    assert "invalid" in response.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_ai_analysis_rejects_unsupported_topic(async_client: AsyncClient) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-topic@example.com", "AI-TOPIC")

    response = await async_client.post(
        f"/api/trials/{trial_id}/ai-analysis",
        headers=headers,
        json={"topic": "patient_notes"},
    )

    assert response.status_code == 422
    assert "topic" in " ".join(response.json()["error"]["details"]).lower()


@pytest.mark.asyncio
async def test_ai_analysis_rejects_raw_question_field(async_client: AsyncClient) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-raw-question@example.com", "AI-RAW")

    response = await async_client.post(
        f"/api/trials/{trial_id}/ai-analysis",
        headers=headers,
        json={"topic": "enrollment", "question": "Summarize this patient SYN-001 and email alice@example.com."},
    )

    assert response.status_code == 422
    assert "question" in " ".join(response.json()["error"]["details"]).lower()


@pytest.mark.asyncio
async def test_ai_analysis_does_not_send_raw_questions_or_identifiers_to_provider(async_client: AsyncClient, db_session) -> None:
    headers, trial_id = await _create_user_and_trial(async_client, "ai-privacy-boundary@example.com", "AI-BOUNDARY")
    db_session.add_all(
        [
            Participant(trial_id=trial_id, participant_id="P-001", status="completed"),
            Participant(trial_id=trial_id, participant_id="P-002", status="active"),
        ]
    )
    db_session.commit()

    with patch("backend.app.services.gemini_service.generate_ai_insight", new=AsyncMock(return_value={"analysis": "safe summary", "model": "gemini"})) as mock_generate:
        response = await async_client.post(
            f"/api/trials/{trial_id}/ai-analysis",
            headers=headers,
            json={"topic": "enrollment"},
        )

    assert response.status_code == 200
    prompt = mock_generate.call_args[0][0]
    assert "SYN-001" not in prompt
    assert "alice@example.com" not in prompt
    assert "question" not in prompt.lower()
    assert "fixed analysis topic" in prompt.lower()
    assert "total_participants" in prompt.lower()
