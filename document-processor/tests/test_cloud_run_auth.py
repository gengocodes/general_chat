"""Tests for Cloud Run ID token service-to-service authentication."""

from unittest.mock import MagicMock, patch
import httpx
import pytest
from google.auth.exceptions import DefaultCredentialsError

from app.infrastructure.cloud_run_auth import (
    CloudRunIdTokenAuth,
    IdTokenFetchError,
    build_service_auth,
)

SERVICE_URL = "https://general-chat-bucket-manager-abc.a.run.app"
FETCH_PATH = "app.infrastructure.cloud_run_auth.id_token.fetch_id_token_credentials"


def _send(auth: httpx.Auth) -> httpx.Request:
    """Run an httpx request through the auth flow and return the authenticated request."""
    request = httpx.Request("POST", f"{SERVICE_URL}/api/objects/upload")
    return next(auth.auth_flow(request))


def test_build_service_auth_is_noop_when_disabled():
    """Verify local development sends no Authorization header."""
    auth = build_service_auth(SERVICE_URL, iam_auth_enabled=False)
    assert not isinstance(auth, CloudRunIdTokenAuth)
    assert "Authorization" not in _send(auth).headers


def test_id_token_auth_attaches_bearer_token_for_service_audience():
    """Verify the Bearer ID token is attached and scoped to the service URL audience."""
    credentials = MagicMock(valid=True, token="signed-id-token")
    with patch(FETCH_PATH, return_value=credentials) as fetch:
        auth = build_service_auth(f"{SERVICE_URL}/", iam_auth_enabled=True)
        request = _send(auth)

    assert request.headers["Authorization"] == "Bearer signed-id-token"
    assert fetch.call_args.args[0] == SERVICE_URL


def test_id_token_auth_refreshes_expired_credentials_and_caches_them():
    """Verify credentials are created once and refreshed only when no longer valid."""
    credentials = MagicMock(valid=False, token="fresh-token")
    with patch(FETCH_PATH, return_value=credentials) as fetch:
        auth = CloudRunIdTokenAuth(SERVICE_URL)
        _send(auth)
        _send(auth)

    assert fetch.call_count == 1
    assert credentials.refresh.call_count == 2


def test_id_token_auth_failure_surfaces_as_httpx_error():
    """Verify token failures raise httpx.HTTPError so adapters map them to domain errors."""
    with patch(FETCH_PATH, side_effect=DefaultCredentialsError("no metadata server")):
        auth = CloudRunIdTokenAuth(SERVICE_URL)
        with pytest.raises(IdTokenFetchError):
            _send(auth)
