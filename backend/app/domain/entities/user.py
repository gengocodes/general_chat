"""Domain entities for authenticated users and Google profiles."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    """A signed-in GenChat user."""

    id: uuid.UUID
    email: str
    name: str


@dataclass(frozen=True)
class GoogleProfile:
    """Identity claims extracted from a verified Google ID token."""

    google_id: str
    email: str
    email_verified: bool
    name: str


@dataclass(frozen=True)
class LoginResult:
    """Outcome of a successful Google sign-in."""

    user: AuthenticatedUser
    session_token: str


@dataclass(frozen=True)
class SessionState:
    """Authentication state of the current browser session.

    `user` is None for guests (absence is a legitimate domain state). `login_required`
    is True when a guest has used every free message.
    """

    user: AuthenticatedUser | None
    login_required: bool
