"""Tests for Alembic schema migrations (AC-064)."""

import importlib
import os
import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

app_config = importlib.import_module("backend.app.core.config")

os.environ["APP_ENV"] = "testing"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL must be set to a PostgreSQL URL before running migration tests. "
        "SQLite is not allowed in APP_ENV=testing."
    )
if TEST_DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "TEST_DATABASE_URL must use PostgreSQL for migration tests; SQLite fallback is prohibited."
    )
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
importlib.reload(app_config)


def _create_isolated_test_database(base_database_url: str) -> tuple[str, str]:
    """Create a temporary PostgreSQL database so migration tests do not collide with app test state."""
    base_url = make_url(base_database_url)
    database_name = f"{base_url.database}_migration_{uuid.uuid4().hex[:8]}"
    admin_url = str(base_url.set(database="postgres"))
    admin_engine = create_engine(admin_url)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    return str(base_url.set(database=database_name)), database_name


def _drop_database(database_name: str, admin_database_url: str) -> None:
    """Drop only the temporary migration database created for this test."""
    admin_engine = create_engine(admin_database_url)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))


def test_alembic_migrations_lifecycle() -> None:
    """AC-064: Migrations upgrade to head and downgrade cleanly without errors."""
    isolated_database_url, database_name = _create_isolated_test_database(TEST_DATABASE_URL)
    admin_database_url = str(make_url(TEST_DATABASE_URL).set(database="postgres"))
    assert isolated_database_url != TEST_DATABASE_URL
    assert isolated_database_url.startswith("postgresql")
    os.environ["TEST_DATABASE_URL"] = isolated_database_url
    app_config = importlib.import_module("backend.app.core.config")
    importlib.reload(app_config)

    try:
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        alembic_cfg = Config(os.path.abspath(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", isolated_database_url)

        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "base")
        command.upgrade(alembic_cfg, "head")
    finally:
        _drop_database(database_name, admin_database_url)
        os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
        app_config = importlib.import_module("backend.app.core.config")
        importlib.reload(app_config)
