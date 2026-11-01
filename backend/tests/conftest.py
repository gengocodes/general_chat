"""Pytest test configuration and fixtures."""

import os
from collections.abc import Iterator

import pytest


# Ensure required environment variables for test execution
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("GEMINI_MODEL", "gemini-test-model")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
os.environ.setdefault("BUCKET_MANAGER_URL", "http://bucket-manager.test:8001")
os.environ.setdefault("DOCUMENT_PROCESSOR_URL", "http://document-processor.test:8002")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test"
)
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-that-is-at-least-32-chars")
# TestClient speaks plain HTTP, so Secure cookies would never be sent back.
os.environ.setdefault("COOKIE_SECURE", "false")


@pytest.fixture(autouse=True)
def in_memory_auth_state() -> Iterator[None]:
    """Run every test against in-memory guest/user stores instead of PostgreSQL."""
    # Imported here so the environment variables above are set before settings load.
    # pylint: disable=import-outside-toplevel
    from app.main import app
    from app.presentation import dependencies
    from tests.fakes import InMemoryGuestUsage, InMemoryUserRepository

    guests = InMemoryGuestUsage()
    users = InMemoryUserRepository()
    app.dependency_overrides[dependencies.get_guest_usage_repository] = lambda: guests
    app.dependency_overrides[dependencies.get_user_repository] = lambda: users
    yield
    app.dependency_overrides.pop(dependencies.get_guest_usage_repository, None)
    app.dependency_overrides.pop(dependencies.get_user_repository, None)
    app.dependency_overrides.pop(dependencies.get_google_verifier, None)
    for limiter in (
        dependencies.auth_rate_limiter,
        dependencies.chat_rate_limiter,
        dependencies.upload_rate_limiter,
        dependencies.download_rate_limiter,
    ):
        limiter.reset()
