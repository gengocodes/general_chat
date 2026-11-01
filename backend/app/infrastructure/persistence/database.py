"""SQLAlchemy engine and session factory construction."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a session factory suited to Neon (pooled, scale-to-zero) PostgreSQL."""
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        # Neon's PgBouncer pooler does not support server-side prepared statements.
        connect_args={"prepare_threshold": None},
    )
    return sessionmaker(engine, expire_on_commit=False)
