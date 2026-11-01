"""Domain entities identifying who is making a request."""

import uuid
from dataclasses import dataclass
from datetime import timedelta

# A guest identity must outlive the browsing session, otherwise the quota would reset.
GUEST_IDENTITY_LIFETIME = timedelta(days=365)


@dataclass(frozen=True)
class UserPrincipal:
    """A signed-in user."""

    user_id: uuid.UUID


@dataclass(frozen=True)
class GuestPrincipal:
    """An anonymous visitor limited to a number of free messages."""

    guest_id: uuid.UUID


Principal = UserPrincipal | GuestPrincipal


@dataclass(frozen=True)
class ResolvedPrincipal:
    """A request principal plus, for brand-new guests only, the token to hand back.

    `new_guest_token` is None when the request already carried a valid identity.
    """

    principal: Principal
    new_guest_token: str | None
