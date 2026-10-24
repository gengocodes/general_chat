"""Unit and API integration tests for per-IP sliding-window rate limiting."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.application.use_cases.chat import StreamChatMessageUseCase
from app.domain.events import StreamCompleteEvent
from app.presentation.dependencies import (
    chat_rate_limiter,
    get_stream_chat_use_case,
)
from app.presentation.rate_limit import SlidingWindowRateLimiter, extract_client_ip

client = TestClient(app)


def _request_with(headers: dict[str, str], host: str | None) -> MagicMock:
    request = MagicMock()
    request.headers = headers
    request.client = MagicMock(host=host) if host else None
    return request


def test_extract_client_ip_prefers_first_forwarded_hop():
    """Verify X-Forwarded-For first hop wins, then socket peer, then 'unknown'."""
    forwarded = _request_with(
        {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}, "10.0.0.2"
    )
    assert extract_client_ip(forwarded) == "203.0.113.5"
    assert extract_client_ip(_request_with({}, "198.51.100.7")) == "198.51.100.7"
    assert extract_client_ip(_request_with({}, None)) == "unknown"


def test_limiter_blocks_after_quota_and_isolates_clients():
    """Verify the quota is enforced per client IP and Retry-After is positive."""
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    limiter.check("1.1.1.1")
    limiter.check("1.1.1.1")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("1.1.1.1")
    assert exc_info.value.status_code == 429
    assert int(exc_info.value.headers["Retry-After"]) >= 1

    limiter.check("2.2.2.2")


def test_limiter_allows_requests_after_window_expires():
    """Verify old timestamps leave the sliding window and free quota."""
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
    with patch("app.presentation.rate_limit.time.monotonic", return_value=1000.0):
        limiter.check("1.1.1.1")
    with patch("app.presentation.rate_limit.time.monotonic", return_value=1061.0):
        limiter.check("1.1.1.1")


def test_chat_endpoint_returns_429_with_retry_after():
    """Verify the chat route returns HTTP 429 and Retry-After once the limit is exceeded."""
    strict_limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

    async def fake_stream(*_args, **_kwargs):
        yield StreamCompleteEvent()

    mock_use_case = MagicMock(spec=StreamChatMessageUseCase)
    mock_use_case.execute = fake_stream

    app.dependency_overrides[get_stream_chat_use_case] = lambda: mock_use_case
    app.dependency_overrides[chat_rate_limiter] = strict_limiter
    try:
        headers = {"X-Forwarded-For": "203.0.113.42"}
        statuses = [
            client.post(
                "/api/chat/stream", json={"message": str(i)}, headers=headers
            )
            for i in range(3)
        ]
        assert [r.status_code for r in statuses] == [200, 200, 429]
        assert int(statuses[2].headers["Retry-After"]) >= 1
    finally:
        app.dependency_overrides.pop(get_stream_chat_use_case, None)
        app.dependency_overrides.pop(chat_rate_limiter, None)
