"""Outbound port for issuing and verifying signed session and guest tokens."""

import uuid
from abc import ABC, abstractmethod

from app.domain.entities.principal import GuestPrincipal, UserPrincipal


class SessionTokenPort(ABC):
    """Issues and verifies signed identity tokens."""

    @abstractmethod
    def issue_user_token(self, user_id: uuid.UUID) -> str:
        """Create a signed session token for a signed-in user."""

    @abstractmethod
    def issue_guest_token(self, guest_id: uuid.UUID) -> str:
        """Create a signed token identifying an anonymous guest."""

    @abstractmethod
    def verify_user_token(self, token: str) -> UserPrincipal:
        """Validate a session token. Raises InvalidCredentialError."""

    @abstractmethod
    def verify_guest_token(self, token: str) -> GuestPrincipal:
        """Validate a guest token. Raises InvalidCredentialError."""
