"""HttpOnly cookie helpers for the session and guest identity tokens."""

from datetime import timedelta

from fastapi import Request, Response

from app.config import settings
from app.domain.entities.principal import GUEST_IDENTITY_LIFETIME

_SESSION_COOKIE = "genchat_session"
_GUEST_COOKIE = "genchat_guest"
_HOST_PREFIX = "__Host-"


def _name(base: str) -> str:
    # The __Host- prefix requires Secure, so it is only used when cookies are Secure.
    return f"{_HOST_PREFIX}{base}" if settings.COOKIE_SECURE else base


def _set(response: Response, base: str, token: str, lifetime: timedelta) -> None:
    response.set_cookie(
        key=_name(base),
        value=token,
        max_age=int(lifetime.total_seconds()),
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


def set_session_cookie(response: Response, token: str) -> None:
    """Attach the signed-in session cookie."""
    _set(response, _SESSION_COOKIE, token, timedelta(days=settings.SESSION_LIFETIME_DAYS))


def set_guest_cookie(response: Response, token: str) -> None:
    """Attach the anonymous guest identity cookie."""
    _set(response, _GUEST_COOKIE, token, GUEST_IDENTITY_LIFETIME)


def clear_session_cookie(response: Response) -> None:
    """Remove the signed-in session cookie."""
    response.delete_cookie(
        key=_name(_SESSION_COOKIE),
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


def read_session_token(request: Request) -> str | None:
    """Return the raw session token cookie, if present."""
    return request.cookies.get(_name(_SESSION_COOKIE))


def read_guest_token(request: Request) -> str | None:
    """Return the raw guest token cookie, if present."""
    return request.cookies.get(_name(_GUEST_COOKIE))
