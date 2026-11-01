"""Use case for signing a user in with a Google ID token."""

from app.application.ports.google_token_verifier_port import GoogleTokenVerifierPort
from app.application.ports.session_token_port import SessionTokenPort
from app.application.ports.user_repository_port import UserRepositoryPort
from app.domain.entities.user import LoginResult
from app.domain.errors import UnverifiedEmailError


class GoogleLoginUseCase:  # pylint: disable=too-few-public-methods
    """Verify a Google credential, register or refresh the user, and issue a session."""

    def __init__(
        self,
        verifier: GoogleTokenVerifierPort,
        users: UserRepositoryPort,
        tokens: SessionTokenPort,
    ):
        self._verifier = verifier
        self._users = users
        self._tokens = tokens

    def execute(self, credential: str) -> LoginResult:
        """Raises InvalidCredentialError, UnverifiedEmailError or PersistenceError."""
        profile = self._verifier.verify(credential)
        if not profile.email_verified:
            raise UnverifiedEmailError("Google email is not verified.")
        user = self._users.register_login(profile)
        return LoginResult(user=user, session_token=self._tokens.issue_user_token(user.id))
