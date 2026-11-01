"""In-memory fakes of the persistence ports for use-case and API tests."""

import threading
import uuid

from app.application.ports.guest_usage_port import GuestUsagePort
from app.application.ports.user_repository_port import UserRepositoryPort
from app.domain.entities.user import AuthenticatedUser, GoogleProfile


class InMemoryGuestUsage(GuestUsagePort):
    """Thread-safe in-memory guest usage store."""

    def __init__(self) -> None:
        self._counts: dict[uuid.UUID, int] = {}
        self._lock = threading.Lock()

    def used_count(self, guest_id: uuid.UUID) -> int:
        return self._counts.get(guest_id, 0)

    def try_consume(self, guest_id: uuid.UUID, limit: int) -> bool:
        with self._lock:
            used = self._counts.get(guest_id, 0)
            if used >= limit:
                return False
            self._counts[guest_id] = used + 1
            return True


class InMemoryUserRepository(UserRepositoryPort):
    """In-memory user store keyed by Google subject."""

    def __init__(self) -> None:
        self.users: dict[str, AuthenticatedUser] = {}
        self.login_count = 0

    def register_login(self, profile: GoogleProfile) -> AuthenticatedUser:
        self.login_count += 1
        existing = self.users.get(profile.google_id)
        if existing is not None:
            return existing
        user = AuthenticatedUser(id=uuid.uuid4(), email=profile.email, name=profile.name)
        self.users[profile.google_id] = user
        return user

    def get_by_id(self, user_id: uuid.UUID) -> AuthenticatedUser | None:
        return next((u for u in self.users.values() if u.id == user_id), None)
