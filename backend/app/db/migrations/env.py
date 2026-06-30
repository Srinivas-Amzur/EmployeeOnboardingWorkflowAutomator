"""
Alembic initialization and migration configuration.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

from dotenv import dotenv_values

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.models import (
    User,
    Employee,
    OnboardingMeeting,
    Notification,
    OnboardingWorkflow,
    OnboardingOrchestrationEvent,
    OnboardingTask,
)

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """Resolve database URL from environment or backend .env file."""
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        backend_root = Path(__file__).resolve().parents[3]
        env_values = dotenv_values(backend_root / ".env")
        database_url = env_values.get("DATABASE_URL", "")

    # Alembic requires a synchronous SQLAlchemy driver.
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)

    # Convert asyncpg-specific ssl param to psycopg2's sslmode param.
    database_url = database_url.replace("?ssl=require", "?sslmode=require")
    database_url = database_url.replace("&ssl=require", "&sslmode=require")

    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url() or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
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
