"""Tests for Alembic schema migrations (AC-064)."""

import os
from alembic.config import Config
from alembic import command


def test_alembic_migrations_lifecycle() -> None:
    """AC-064: Migrations upgrade to head and downgrade cleanly without errors."""
    alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
    alembic_cfg = Config(os.path.abspath(alembic_ini_path))

    # Test upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Test downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Re-apply upgrade to leave schema at head
    command.upgrade(alembic_cfg, "head")
