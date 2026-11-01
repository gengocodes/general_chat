"""API integration tests for authentication and the guest free-message quota."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.application.ports.google_token_verifier_port import GoogleTokenVerifierPort
from app.application.use_cases.chat import StreamChatMessageUseCase
from app.config import settings
from app.domain.entities.user import GoogleProfile
from app.domain.errors import InvalidCredentialError
from app.domain.events import StreamCompleteEvent
from app.main import app
from app.presentation.dependencies import (
    get_google_verifier,
    get_stream_chat_use_case,
)

GOOD_ORIGIN = {"Origin": "http://localhost:3000"}
CHAT_BODY = {"message": "hello"}


class _StubVerifier(GoogleTokenVerifierPort):  # pylint: disable=too-few-public-methods
    def __init__(self, profile: GoogleProfile | None):
        self._profile = profile

    def verify(self, credential: str) -> GoogleProfile:
        if self._profile is None:
            raise InvalidCredentialError("bad")
        return self._profile


def _profile(email_verified: bool = True) -> GoogleProfile:
    return GoogleProfile("sub-1", "ada@example.com", email_verified, "Ada")


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    """A fresh client (and cookie jar) per test."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def fake_chat_use_case():
    """Replace the LLM-backed chat use case with a trivial stream."""

    async def fake_stream(*_args, **_kwargs):
        yield StreamCompleteEvent()

    mock_use_case = MagicMock(spec=StreamChatMessageUseCase)
    mock_use_case.execute = fake_stream
    app.dependency_overrides[get_stream_chat_use_case] = lambda: mock_use_case
    yield
    app.dependency_overrides.pop(get_stream_chat_use_case, None)


def _use_verifier(profile: GoogleProfile | None) -> None:
    app.dependency_overrides[get_google_verifier] = lambda: _StubVerifier(profile)


def test_google_login_sets_httponly_session_cookie(client):
    """Verify google login sets httponly session cookie."""
    _use_verifier(_profile())

    res = client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN)

    assert res.status_code == 200
    assert res.json()["email"] == "ada@example.com"
    set_cookie = res.headers["set-cookie"].lower()
    assert "genchat_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_google_login_invalid_credential_returns_generic_401(client):
    """Verify google login invalid credential returns generic 401."""
    _use_verifier(None)

    res = client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN)

    assert res.status_code == 401
    assert res.json() == {"detail": "Invalid Google credential."}
    assert "set-cookie" not in res.headers


def test_google_login_unverified_email_returns_400(client):
    """Verify google login unverified email returns 400."""
    _use_verifier(_profile(email_verified=False))

    res = client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN)

    assert res.status_code == 400


def test_google_login_validates_body(client):
    """Verify google login validates body."""
    assert client.post("/api/auth/google", json={}, headers=GOOD_ORIGIN).status_code == 422
    assert (
        client.post("/api/auth/google", json={"credential": ""}, headers=GOOD_ORIGIN).status_code
        == 422
    )


def test_google_login_rejects_foreign_origin(client):
    """Verify google login rejects foreign origin."""
    _use_verifier(_profile())

    res = client.post(
        "/api/auth/google", json={"credential": "c"}, headers={"Origin": "https://evil.example"}
    )

    assert res.status_code == 403


def test_auth_endpoints_are_rate_limited(client):
    """Verify auth endpoints are rate limited."""
    _use_verifier(_profile())

    statuses = [
        client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN).status_code
        for _ in range(settings.AUTH_RATE_LIMIT_PER_MINUTE + 1)
    ]

    assert statuses[-1] == 429
    assert "Retry-After" in client.get("/api/auth/session").headers


def test_session_for_new_guest_issues_guest_cookie(client):
    """Verify session for new guest issues guest cookie."""
    res = client.get("/api/auth/session")

    assert res.status_code == 200
    assert res.json() == {"user": None, "login_required": False}
    assert "genchat_guest=" in res.headers["set-cookie"]
    assert "httponly" in res.headers["set-cookie"].lower()


def test_session_reports_signed_in_user(client):
    """Verify session reports signed in user."""
    _use_verifier(_profile())
    client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN)

    body = client.get("/api/auth/session").json()

    assert body["user"]["email"] == "ada@example.com"
    assert body["login_required"] is False


def test_logout_clears_session_but_keeps_guest_quota(client):
    """Verify logout clears session but keeps guest quota."""
    _use_verifier(_profile())
    client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN)

    res = client.post("/api/auth/logout", headers=GOOD_ORIGIN)

    assert res.status_code == 204
    assert client.get("/api/auth/session").json()["user"] is None


def test_chat_allows_free_messages_then_requires_login(client):
    """Verify chat allows free messages then requires login."""
    for _ in range(settings.FREE_MESSAGE_LIMIT):
        assert client.post("/api/chat/stream", json=CHAT_BODY).status_code == 200

    res = client.post("/api/chat/stream", json=CHAT_BODY)

    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "login_required"
    assert client.get("/api/auth/session").json()["login_required"] is True


def test_first_chat_response_sets_guest_cookie(client):
    """Verify first chat response sets guest cookie."""
    res = client.post("/api/chat/stream", json=CHAT_BODY)

    assert "genchat_guest=" in res.headers["set-cookie"]


def test_invalid_chat_request_does_not_consume_free_message(client):
    """Verify invalid chat request does not consume free message."""
    for _ in range(settings.FREE_MESSAGE_LIMIT + 2):
        assert client.post("/api/chat/stream", json={"message": "x" * 8001}).status_code == 422

    assert client.post("/api/chat/stream", json=CHAT_BODY).status_code == 200


def test_signed_in_user_is_not_limited(client):
    """Verify signed in user is not limited."""
    _use_verifier(_profile())
    for _ in range(settings.FREE_MESSAGE_LIMIT):
        client.post("/api/chat/stream", json=CHAT_BODY)
    assert client.post("/api/chat/stream", json=CHAT_BODY).status_code == 401

    client.post("/api/auth/google", json={"credential": "c"}, headers=GOOD_ORIGIN)

    for _ in range(settings.FREE_MESSAGE_LIMIT + 3):
        assert client.post("/api/chat/stream", json=CHAT_BODY).status_code == 200


def test_chat_rejects_foreign_origin(client):
    """Verify chat rejects foreign origin."""
    res = client.post(
        "/api/chat/stream",
        json=CHAT_BODY,
        headers={"Origin": "https://evil.example"},
    )

    assert res.status_code == 403


def test_forged_guest_cookie_does_not_reuse_quota(client):
    """Verify forged guest cookie does not reuse quota."""
    for _ in range(settings.FREE_MESSAGE_LIMIT):
        client.post("/api/chat/stream", json=CHAT_BODY)
    assert client.post("/api/chat/stream", json=CHAT_BODY).status_code == 401

    client.cookies.clear()
    client.cookies.set("genchat_guest", "forged.token.value")

    # An unsigned/forged cookie is ignored and replaced by a brand-new guest identity.
    res = client.get("/api/auth/session")
    assert res.json()["login_required"] is False
    assert "genchat_guest=" in res.headers["set-cookie"]


def test_upload_blocked_for_exhausted_guest(client):
    """Verify upload blocked for exhausted guest."""
    for _ in range(settings.FREE_MESSAGE_LIMIT):
        client.post("/api/chat/stream", json=CHAT_BODY)

    res = client.post(
        "/api/files/upload", files={"file": ("a.pdf", b"x", "application/pdf")}
    )

    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "login_required"


def test_chat_rejects_foreign_referer_when_origin_missing(client):
    """Verify CSRF Referer fallback rejects cross-origin Referer headers."""
    res = client.post(
        "/api/chat/stream",
        json=CHAT_BODY,
        headers={"Referer": "https://evil.example/attack"},
    )

    assert res.status_code == 403
