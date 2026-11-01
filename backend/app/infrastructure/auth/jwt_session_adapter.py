"""HS256 JWT adapter for signed-in session tokens and anonymous guest tokens."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.application.ports.session_token_port import SessionTokenPort
from app.domain.entities.principal import (
    GUEST_IDENTITY_LIFETIME,
    GuestPrincipal,
    UserPrincipal,
)
from app.domain.errors import InvalidCredentialError

_ALGORITHM = "HS256"
_USER_AUDIENCE = "genchat:user"
_GUEST_AUDIENCE = "genchat:guest"
_REQUIRED_CLAIMS = ["exp", "iat", "sub", "aud"]


class JwtSessionAdapter(SessionTokenPort):
    """Signs and verifies tokens. Guest and user tokens use distinct audiences."""

    def __init__(self, secret: str, user_lifetime: timedelta):
        self._secret = secret
        self._user_lifetime = user_lifetime

    def issue_user_token(self, user_id: uuid.UUID) -> str:
        return self._encode(str(user_id), _USER_AUDIENCE, self._user_lifetime)

    def issue_guest_token(self, guest_id: uuid.UUID) -> str:
        return self._encode(str(guest_id), _GUEST_AUDIENCE, GUEST_IDENTITY_LIFETIME)

    def verify_user_token(self, token: str) -> UserPrincipal:
        return UserPrincipal(user_id=self._decode(token, _USER_AUDIENCE))

    def verify_guest_token(self, token: str) -> GuestPrincipal:
        return GuestPrincipal(guest_id=self._decode(token, _GUEST_AUDIENCE))

    def _encode(self, subject: str, audience: str, lifetime: timedelta) -> str:
        now = datetime.now(timezone.utc)
        claims = {"sub": subject, "aud": audience, "iat": now, "exp": now + lifetime}
        return jwt.encode(claims, self._secret, algorithm=_ALGORITHM)

    def _decode(self, token: str, audience: str) -> uuid.UUID:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
                audience=audience,
                options={"require": _REQUIRED_CLAIMS},
            )
            return uuid.UUID(str(claims["sub"]))
        except (jwt.PyJWTError, ValueError) as exc:
            raise InvalidCredentialError("Invalid or expired token.") from exc
