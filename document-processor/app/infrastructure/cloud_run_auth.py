"""
Cloud Run service-to-service authentication.

Private Cloud Run services (`--no-allow-unauthenticated`) reject any request that lacks a
Google-signed ID token in the `Authorization: Bearer` header *before* the container is reached.
This is independent of, and complements, the application-level `X-Internal-API-Key` check.
"""

from collections.abc import Generator
import threading

import httpx
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token


class IdTokenFetchError(httpx.HTTPError):
    """Raised when a Google ID token cannot be obtained for the target service."""


class CloudRunIdTokenAuth(httpx.Auth):
    """httpx auth flow attaching a Google-signed ID token scoped to one Cloud Run service URL."""

    def __init__(self, audience: str):
        self._audience = audience.rstrip("/")
        self._credentials: Credentials | None = None
        self._lock = threading.Lock()

    def _bearer_token(self) -> str:
        """Return a valid ID token, creating or refreshing cached credentials when needed."""
        with self._lock:
            try:
                if self._credentials is None:
                    self._credentials = id_token.fetch_id_token_credentials(
                        self._audience, request=GoogleAuthRequest()
                    )
                if not self._credentials.valid:
                    self._credentials.refresh(GoogleAuthRequest())
            except GoogleAuthError as exc:
                raise IdTokenFetchError(
                    f"Could not obtain ID token for audience {self._audience}."
                ) from exc
            return str(self._credentials.token)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self._bearer_token()}"
        yield request


def build_service_auth(service_url: str, iam_auth_enabled: bool) -> httpx.Auth:
    """
    Build the httpx auth for calling an internal service.

    Returns a Cloud Run ID token auth when IAM auth is enabled; otherwise the no-op base
    `httpx.Auth` (local development / docker-compose without Cloud Run IAM).
    """
    if iam_auth_enabled:
        return CloudRunIdTokenAuth(service_url)
    return httpx.Auth()
