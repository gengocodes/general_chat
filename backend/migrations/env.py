"""Alembic environment: runs migrations against DATABASE_MIGRATION_URL (direct connection)."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.infrastructure.persistence.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _migration_url() -> str:
    """Return the direct (non-pooled) database URL used for DDL."""
    url = os.environ.get("DATABASE_MIGRATION_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_MIGRATION_URL is required to run migrations "
            "(use the direct, non-pooler connection string)."
        )
    return url


def run_migrations_offline() -> None:
    """Emit migration SQL without connecting to the database."""
    context.configure(
        url=_migration_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations through a live connection."""
    engine = create_engine(_migration_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
