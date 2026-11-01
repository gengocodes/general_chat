"""Google Sign-In ID token verification adapter."""

import logging

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.application.ports.google_token_verifier_port import GoogleTokenVerifierPort
from app.domain.entities.user import GoogleProfile
from app.domain.errors import InvalidCredentialError

logger = logging.getLogger(__name__)

_CLOCK_SKEW_SECONDS = 10
_ALLOWED_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


class GoogleTokenVerifierAdapter(GoogleTokenVerifierPort):  # pylint: disable=too-few-public-methods
    """Verifies ID tokens (signature, expiry, issuer and audience) with google-auth."""

    def __init__(self, client_id: str):
        self._client_id = client_id

    def verify(self, credential: str) -> GoogleProfile:
        try:
            payload = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                credential,
                google_requests.Request(),
                self._client_id,
                clock_skew_in_seconds=_CLOCK_SKEW_SECONDS,
            )
        except (ValueError, GoogleAuthError) as exc:
            # Log only the error class: messages can echo token contents.
            logger.warning("Google ID token verification failed: %s", type(exc).__name__)
            raise InvalidCredentialError("Invalid Google credential.") from exc
        return self._to_profile(payload)

    @staticmethod
    def _to_profile(payload: dict[str, object]) -> GoogleProfile:
        issuer = str(payload.get("iss") or "").strip()
        if issuer not in _ALLOWED_ISSUERS:
            raise InvalidCredentialError("Invalid Google token issuer.")
        google_id = str(payload.get("sub") or "").strip()
        email = str(payload.get("email") or "").strip().lower()
        if not google_id or not email:
            raise InvalidCredentialError("Google profile is missing required claims.")
        name = str(payload.get("name") or "").strip() or email.split("@", maxsplit=1)[0]
        return GoogleProfile(
            google_id=google_id,
            email=email,
            email_verified=payload.get("email_verified") is True,
            name=name,
        )
