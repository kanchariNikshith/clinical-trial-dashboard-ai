import os
import sys
from logging.config import fileConfig
from pathlib import Path

app_env = os.getenv("APP_ENV", "testing").lower()
if app_env != "testing":
    raise RuntimeError(
        "Alembic must run with APP_ENV=testing. SQLite and production targets are not allowed. "
        "Set TEST_DATABASE_URL to a PostgreSQL URL before running migrations."
    )

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is required when APP_ENV=testing. Set a PostgreSQL test database URL; "
        "SQLite is not allowed."
    )
if TEST_DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "SQLite is not allowed for APP_ENV=testing. Configure a PostgreSQL TEST_DATABASE_URL for Alembic."
    )

os.environ["APP_ENV"] = "testing"
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure workspace root is in sys.path for editable installs and local execution.
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

sys.modules.pop("backend.app.core.config", None)
from backend.app.core.config import settings
from backend.app.db.base import Base

import backend.app.models  # Ensure all models are registered on Base.metadata

config = context.config

# Overwrite sqlalchemy.url with the resolved application settings.
config.set_main_option("sqlalchemy.url", settings.effective_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.effective_database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
