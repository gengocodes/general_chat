"""Outbound port for persisting users."""

import uuid
from abc import ABC, abstractmethod

from app.domain.entities.user import AuthenticatedUser, GoogleProfile


class UserRepositoryPort(ABC):
    """Persistence contract for users. Raises PersistenceError on database failure."""

    @abstractmethod
    def register_login(self, profile: GoogleProfile) -> AuthenticatedUser:
        """Atomically create the user for this Google account or refresh its last login."""

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> AuthenticatedUser | None:
        """Return the user, or None if it no longer exists."""
