"""Outbound port for verifying Google Sign-In ID tokens."""

from abc import ABC, abstractmethod

from app.domain.entities.user import GoogleProfile


class GoogleTokenVerifierPort(ABC):  # pylint: disable=too-few-public-methods
    """Verifies a Google ID token and extracts the profile claims."""

    @abstractmethod
    def verify(self, credential: str) -> GoogleProfile:
        """Return the verified profile. Raises InvalidCredentialError."""
