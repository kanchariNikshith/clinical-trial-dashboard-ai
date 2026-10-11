"""Pytest fixtures for database isolation and test client."""

import os
from pathlib import Path
from typing import Generator

from alembic import command
from alembic.config import Config

if os.getenv("APP_ENV") and os.getenv("APP_ENV").lower() != "testing":
    raise RuntimeError(
        "pytest must run with APP_ENV=testing. Refusing to target a development or production database."
    )
os.environ["APP_ENV"] = "testing"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is required for pytest and must point to PostgreSQL. "
        "SQLite and default development URLs are not allowed in APP_ENV=testing."
    )
if TEST_DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "TEST_DATABASE_URL must use PostgreSQL, not SQLite. Configure an isolated test database URL."
    )
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app

import backend.app.models  # Register all models on Base.metadata

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", settings.TEST_DATABASE_URL)
test_engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def reset_test_schema() -> None:
    """Reset only the dedicated PostgreSQL test schema so the migration chain is repeatable."""
    with create_engine(TEST_DB_URL).begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create the schema once for the session using Alembic migrations, not create_all()."""
    reset_test_schema()
    project_root = Path(__file__).resolve().parents[1]
    alembic_ini_path = project_root / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(alembic_cfg, "head")
    yield
    reset_test_schema()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transaction-scoped session for each test without rebuilding tables."""
    connection = test_engine.connect()
    connection.begin()
    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        if connection.in_transaction():
            connection.rollback()
        connection.close()


@pytest.fixture
def async_client(db_session: Session) -> Generator[AsyncClient, None, None]:
    """Provide an AsyncClient with overridden database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    app.dependency_overrides.clear()
