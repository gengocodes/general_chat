"""Outbound port for tracking free messages consumed by guests."""

import uuid
from abc import ABC, abstractmethod


class GuestUsagePort(ABC):
    """Persistence contract for guest message quotas. Raises PersistenceError on failure."""

    @abstractmethod
    def used_count(self, guest_id: uuid.UUID) -> int:
        """Return how many free messages this guest has consumed."""

    @abstractmethod
    def try_consume(self, guest_id: uuid.UUID, limit: int) -> bool:
        """Atomically consume one message if fewer than `limit` were used.

        Returns False, without changing state, when the quota is exhausted.
        """
