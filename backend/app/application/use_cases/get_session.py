"""Use case describing the authentication state of the current session."""

from app.application.ports.user_repository_port import UserRepositoryPort
from app.application.use_cases.chat_access import ChatAccessUseCase
from app.domain.entities.principal import Principal, UserPrincipal
from app.domain.entities.user import SessionState


class GetSessionUseCase:  # pylint: disable=too-few-public-methods
    """Report the signed-in user, or whether a guest must sign in."""

    def __init__(self, users: UserRepositoryPort, access: ChatAccessUseCase):
        self._users = users
        self._access = access

    def execute(self, principal: Principal) -> SessionState:
        """Return the session state for the principal."""
        if isinstance(principal, UserPrincipal):
            user = self._users.get_by_id(principal.user_id)
            # A valid token for a deleted user must sign in again.
            return SessionState(user=user, login_required=user is None)
        return SessionState(user=None, login_required=self._access.is_login_required(principal))
