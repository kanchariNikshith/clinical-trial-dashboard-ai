"""Tests for health check and error envelope."""

import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app




@pytest.mark.asyncio
async def test_root_health_endpoint() -> None:
    """AC-063: /health returns status: healthy without leaking secrets."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

        # Security check: verify no secrets or internal sensitive configs leaked
        body_text = response.text.lower()
        assert "secret" not in body_text
        assert "password" not in body_text
        assert "database" not in body_text
        assert "gemini" not in body_text
        assert "postgres" not in body_text


@pytest.mark.asyncio
async def test_api_health_endpoint() -> None:
    """Verify /api/health works identically."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_status_endpoint() -> None:
    """Verify root GET / returns online status and navigation links."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "health_url" in data
        assert "docs_url" in data


@pytest.mark.asyncio
async def test_error_envelope_for_404() -> None:
    """Verify non-existent route returns standard JSON error envelope."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/non-existent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "HTTP_404"
        assert "Not Found" in data["error"]["message"]
