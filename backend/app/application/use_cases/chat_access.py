"""Use case enforcing the guest free-message quota."""

from app.application.ports.guest_usage_port import GuestUsagePort
from app.domain.entities.principal import Principal, UserPrincipal
from app.domain.errors import LoginRequiredError


class ChatAccessUseCase:
    """Signed-in users always have access; guests get a limited number of messages."""

    def __init__(self, guests: GuestUsagePort, free_message_limit: int):
        self._guests = guests
        self._limit = free_message_limit

    def is_login_required(self, principal: Principal) -> bool:
        """True when a guest has no free messages left."""
        if isinstance(principal, UserPrincipal):
            return False
        return self._guests.used_count(principal.guest_id) >= self._limit

    def ensure_access(self, principal: Principal) -> None:
        """Read-only check. Raises LoginRequiredError when a guest is out of messages."""
        if self.is_login_required(principal):
            raise LoginRequiredError("Sign in to continue.")

    def consume_message(self, principal: Principal) -> None:
        """Consume one free message for a guest. Raises LoginRequiredError when exhausted."""
        if isinstance(principal, UserPrincipal):
            return
        if not self._guests.try_consume(principal.guest_id, self._limit):
            raise LoginRequiredError("Sign in to continue.")
