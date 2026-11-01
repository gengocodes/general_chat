"""PostgreSQL integration tests: Alembic migrations and repositories.

Requires TEST_DATABASE_URL pointing at a disposable PostgreSQL database (the schema is
dropped and recreated). Skipped when the variable is not set, e.g. in the plain unit run.
"""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.domain.entities.user import GoogleProfile
from app.infrastructure.persistence.database import create_session_factory
from app.infrastructure.persistence.guest_usage_repository import (
    SqlAlchemyGuestUsageRepository,
)
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set (needs PostgreSQL)"
)

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    return config


@pytest.fixture(name="migrated_db")
def migrated_db_fixture(monkeypatch):
    """Apply all migrations to an empty schema and restore clean head state afterwards."""
    monkeypatch.setenv("DATABASE_MIGRATION_URL", TEST_DATABASE_URL)
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield TEST_DATABASE_URL
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def test_migrations_create_and_drop_expected_tables(migrated_db):
    """Verify migrations create and drop expected tables."""
    engine = create_engine(migrated_db)
    assert {"users", "guest_usage"} <= set(inspect(engine).get_table_names())

    command.downgrade(_alembic_config(), "base")

    remaining = set(inspect(engine).get_table_names())
    assert "users" not in remaining
    assert "guest_usage" not in remaining
    engine.dispose()
    command.upgrade(_alembic_config(), "head")


def test_users_schema_has_no_nullable_columns_and_unique_keys(migrated_db):
    """Verify users schema has no nullable columns and unique keys."""
    engine = create_engine(migrated_db)
    columns = inspect(engine).get_columns("users")
    uniques = {tuple(u["column_names"]) for u in inspect(engine).get_unique_constraints("users")}

    assert all(not column["nullable"] for column in columns)
    assert {("email",), ("google_id",)} <= uniques
    engine.dispose()


def test_users_email_must_be_lowercase(migrated_db):
    """Verify users email must be lowercase."""
    engine = create_engine(migrated_db)
    with engine.begin() as connection:
        with pytest.raises(Exception, match="ck_users_email_lowercase"):
            connection.execute(
                text(
                    "INSERT INTO users (id, email, google_id, name) "
                    "VALUES (gen_random_uuid(), 'Mixed@Example.com', 'g', 'n')"
                )
            )
    engine.dispose()


def test_register_login_creates_then_reuses_user(migrated_db):
    """Verify register login creates then reuses user."""
    repo = SqlAlchemyUserRepository(create_session_factory(migrated_db))
    profile = GoogleProfile("sub-1", "ada@example.com", True, "Ada")

    first = repo.register_login(profile)
    second = repo.register_login(profile)

    assert first == second
    assert repo.get_by_id(first.id) == first
    assert repo.get_by_id(uuid.uuid4()) is None


def test_register_login_is_safe_under_concurrency(migrated_db):
    """Verify register login is safe under concurrency."""
    repo = SqlAlchemyUserRepository(create_session_factory(migrated_db))
    profile = GoogleProfile("sub-race", "race@example.com", True, "Race")

    with ThreadPoolExecutor(max_workers=8) as pool:
        users = list(pool.map(lambda _: repo.register_login(profile), range(8)))

    assert len({user.id for user in users}) == 1


def test_try_consume_stops_at_limit(migrated_db):
    """Verify try consume stops at limit."""
    repo = SqlAlchemyGuestUsageRepository(create_session_factory(migrated_db))
    guest = uuid.uuid4()

    assert repo.used_count(guest) == 0
    assert repo.try_consume(guest, 2)
    assert repo.try_consume(guest, 2)
    assert not repo.try_consume(guest, 2)
    assert repo.used_count(guest) == 2


def test_try_consume_never_exceeds_limit_under_concurrency(migrated_db):
    """Verify try consume never exceeds limit under concurrency."""
    repo = SqlAlchemyGuestUsageRepository(create_session_factory(migrated_db))
    guest = uuid.uuid4()

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: repo.try_consume(guest, 2), range(20)))

    assert results.count(True) == 2
    assert repo.used_count(guest) == 2
