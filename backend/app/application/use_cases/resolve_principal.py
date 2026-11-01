"""Use case resolving the request identity from session and guest tokens."""

import uuid

from app.application.ports.session_token_port import SessionTokenPort
from app.domain.entities.principal import (
    GuestPrincipal,
    Principal,
    ResolvedPrincipal,
)
from app.domain.errors import InvalidCredentialError


class ResolvePrincipalUseCase:  # pylint: disable=too-few-public-methods
    """Turn the raw cookie tokens into a Principal, minting a guest identity when needed."""

    def __init__(self, tokens: SessionTokenPort):
        self._tokens = tokens

    def execute(
        self, session_token: str | None, guest_token: str | None
    ) -> ResolvedPrincipal:
        """Prefer a valid session, then a valid guest token, else create a new guest."""
        existing = self._existing_principal(session_token, guest_token)
        if existing is not None:
            return ResolvedPrincipal(principal=existing, new_guest_token=None)
        guest = GuestPrincipal(guest_id=uuid.uuid4())
        return ResolvedPrincipal(
            principal=guest,
            new_guest_token=self._tokens.issue_guest_token(guest.guest_id),
        )

    def _existing_principal(
        self, session_token: str | None, guest_token: str | None
    ) -> Principal | None:
        if session_token:
            try:
                return self._tokens.verify_user_token(session_token)
            except InvalidCredentialError:
                pass
        if guest_token:
            try:
                return self._tokens.verify_guest_token(guest_token)
            except InvalidCredentialError:
                pass
        return None
