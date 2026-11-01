"""Unit tests for authentication and guest-quota use cases and adapters."""

import uuid
from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from google.auth.exceptions import GoogleAuthError

from app.application.ports.google_token_verifier_port import GoogleTokenVerifierPort
from app.application.use_cases.chat_access import ChatAccessUseCase
from app.application.use_cases.get_session import GetSessionUseCase
from app.application.use_cases.google_login import GoogleLoginUseCase
from app.application.use_cases.resolve_principal import ResolvePrincipalUseCase
from app.domain.entities.principal import GuestPrincipal, UserPrincipal
from app.domain.entities.user import GoogleProfile
from app.domain.errors import (
    InvalidCredentialError,
    LoginRequiredError,
    UnverifiedEmailError,
)
from app.infrastructure.auth.google_token_verifier_adapter import (
    GoogleTokenVerifierAdapter,
)
from app.infrastructure.auth.jwt_session_adapter import JwtSessionAdapter
from tests.fakes import InMemoryGuestUsage, InMemoryUserRepository

SECRET = "unit-test-secret-that-is-at-least-32-chars"


class _FakeVerifier(GoogleTokenVerifierPort):  # pylint: disable=too-few-public-methods
    def __init__(self, profile: GoogleProfile | None):
        self._profile = profile

    def verify(self, credential: str) -> GoogleProfile:
        if self._profile is None:
            raise InvalidCredentialError("bad")
        return self._profile


def _profile(email_verified: bool = True) -> GoogleProfile:
    return GoogleProfile(
        google_id="sub-123",
        email="ada@example.com",
        email_verified=email_verified,
        name="Ada",
    )


def _tokens(lifetime: timedelta = timedelta(days=7)) -> JwtSessionAdapter:
    return JwtSessionAdapter(secret=SECRET, user_lifetime=lifetime)


# --- GoogleLoginUseCase ---------------------------------------------------------------


def test_google_login_creates_user_and_issues_session():
    """Verify google login creates user and issues session."""
    users = InMemoryUserRepository()
    tokens = _tokens()
    result = GoogleLoginUseCase(_FakeVerifier(_profile()), users, tokens).execute("cred")

    assert result.user.email == "ada@example.com"
    assert tokens.verify_user_token(result.session_token).user_id == result.user.id


def test_google_login_returning_user_keeps_identity():
    """Verify google login returning user keeps identity."""
    users = InMemoryUserRepository()
    use_case = GoogleLoginUseCase(_FakeVerifier(_profile()), users, _tokens())

    first = use_case.execute("cred")
    second = use_case.execute("cred")

    assert first.user.id == second.user.id
    assert len(users.users) == 1


def test_google_login_rejects_unverified_email():
    """Verify google login rejects unverified email."""
    users = InMemoryUserRepository()
    use_case = GoogleLoginUseCase(
        _FakeVerifier(_profile(email_verified=False)), users, _tokens()
    )

    with pytest.raises(UnverifiedEmailError):
        use_case.execute("cred")
    assert not users.users


def test_google_login_propagates_invalid_credential():
    """Verify google login propagates invalid credential."""
    use_case = GoogleLoginUseCase(_FakeVerifier(None), InMemoryUserRepository(), _tokens())

    with pytest.raises(InvalidCredentialError):
        use_case.execute("cred")


# --- ChatAccessUseCase ----------------------------------------------------------------


def test_guest_gets_exactly_the_free_messages_then_login_required():
    """Verify guest gets exactly the free messages then login required."""
    access = ChatAccessUseCase(InMemoryGuestUsage(), free_message_limit=2)
    guest = GuestPrincipal(uuid.uuid4())

    access.consume_message(guest)
    access.consume_message(guest)
    assert access.is_login_required(guest)
    with pytest.raises(LoginRequiredError):
        access.consume_message(guest)


def test_guest_quota_is_tracked_per_guest():
    """Verify guest quota is tracked per guest."""
    access = ChatAccessUseCase(InMemoryGuestUsage(), free_message_limit=1)
    first, second = GuestPrincipal(uuid.uuid4()), GuestPrincipal(uuid.uuid4())

    access.consume_message(first)

    assert access.is_login_required(first)
    assert not access.is_login_required(second)


def test_signed_in_user_is_never_limited():
    """Verify signed in user is never limited."""
    access = ChatAccessUseCase(InMemoryGuestUsage(), free_message_limit=1)
    user = UserPrincipal(uuid.uuid4())

    for _ in range(5):
        access.consume_message(user)
    access.ensure_access(user)
    assert not access.is_login_required(user)


def test_ensure_access_does_not_consume():
    """Verify ensure access does not consume."""
    access = ChatAccessUseCase(InMemoryGuestUsage(), free_message_limit=1)
    guest = GuestPrincipal(uuid.uuid4())

    access.ensure_access(guest)
    access.ensure_access(guest)
    access.consume_message(guest)
    with pytest.raises(LoginRequiredError):
        access.ensure_access(guest)


# --- ResolvePrincipalUseCase ----------------------------------------------------------


def test_resolve_without_cookies_creates_guest_with_token():
    """Verify resolve without cookies creates guest with token."""
    tokens = _tokens()
    resolved = ResolvePrincipalUseCase(tokens).execute(None, None)

    assert isinstance(resolved.principal, GuestPrincipal)
    assert resolved.new_guest_token is not None
    assert tokens.verify_guest_token(resolved.new_guest_token) == resolved.principal


def test_resolve_reuses_valid_guest_token():
    """Verify resolve reuses valid guest token."""
    tokens = _tokens()
    guest = GuestPrincipal(uuid.uuid4())

    token = tokens.issue_guest_token(guest.guest_id)
    resolved = ResolvePrincipalUseCase(tokens).execute(None, token)

    assert resolved.principal == guest
    assert resolved.new_guest_token is None


def test_resolve_prefers_session_over_guest():
    """Verify resolve prefers session over guest."""
    tokens = _tokens()
    user_id, guest_id = uuid.uuid4(), uuid.uuid4()

    resolved = ResolvePrincipalUseCase(tokens).execute(
        tokens.issue_user_token(user_id), tokens.issue_guest_token(guest_id)
    )

    assert resolved.principal == UserPrincipal(user_id)


def test_resolve_ignores_garbage_tokens_and_mints_new_guest():
    """Verify resolve ignores garbage tokens and mints new guest."""
    resolved = ResolvePrincipalUseCase(_tokens()).execute("garbage", "garbage")

    assert isinstance(resolved.principal, GuestPrincipal)
    assert resolved.new_guest_token is not None


def test_resolve_does_not_accept_guest_token_as_session():
    """Verify resolve does not accept guest token as session."""
    tokens = _tokens()
    guest_token = tokens.issue_guest_token(uuid.uuid4())

    resolved = ResolvePrincipalUseCase(tokens).execute(guest_token, None)

    assert isinstance(resolved.principal, GuestPrincipal)
    assert resolved.new_guest_token is not None


# --- GetSessionUseCase ----------------------------------------------------------------


def test_session_for_signed_in_user():
    """Verify session for signed in user."""
    users = InMemoryUserRepository()
    user = users.register_login(_profile())
    session = GetSessionUseCase(users, ChatAccessUseCase(InMemoryGuestUsage(), 2))

    state = session.execute(UserPrincipal(user.id))

    assert state.user == user
    assert not state.login_required


def test_session_for_deleted_user_requires_login():
    """Verify session for deleted user requires login."""
    session = GetSessionUseCase(
        InMemoryUserRepository(), ChatAccessUseCase(InMemoryGuestUsage(), 2)
    )

    state = session.execute(UserPrincipal(uuid.uuid4()))

    assert state.user is None
    assert state.login_required


def test_session_for_exhausted_guest_requires_login():
    """Verify session for exhausted guest requires login."""
    guests = InMemoryGuestUsage()
    access = ChatAccessUseCase(guests, 1)
    guest = GuestPrincipal(uuid.uuid4())
    session = GetSessionUseCase(InMemoryUserRepository(), access)

    assert not session.execute(guest).login_required
    access.consume_message(guest)
    assert session.execute(guest).login_required


# --- JwtSessionAdapter ----------------------------------------------------------------


def test_jwt_roundtrip():
    """Verify jwt roundtrip."""
    tokens = _tokens()
    user_id, guest_id = uuid.uuid4(), uuid.uuid4()

    assert tokens.verify_user_token(tokens.issue_user_token(user_id)).user_id == user_id
    assert tokens.verify_guest_token(tokens.issue_guest_token(guest_id)).guest_id == guest_id


def test_jwt_rejects_wrong_audience():
    """Verify jwt rejects wrong audience."""
    tokens = _tokens()

    with pytest.raises(InvalidCredentialError):
        tokens.verify_user_token(tokens.issue_guest_token(uuid.uuid4()))
    with pytest.raises(InvalidCredentialError):
        tokens.verify_guest_token(tokens.issue_user_token(uuid.uuid4()))


def test_jwt_rejects_expired_token():
    """Verify jwt rejects expired token."""
    tokens = _tokens(lifetime=timedelta(seconds=-5))

    with pytest.raises(InvalidCredentialError):
        tokens.verify_user_token(tokens.issue_user_token(uuid.uuid4()))


def test_jwt_rejects_wrong_secret_and_tampering():
    """Verify jwt rejects wrong secret and tampering."""
    token = _tokens().issue_user_token(uuid.uuid4())
    other = JwtSessionAdapter(secret="x" * 40, user_lifetime=timedelta(days=1))

    with pytest.raises(InvalidCredentialError):
        other.verify_user_token(token)
    with pytest.raises(InvalidCredentialError):
        _tokens().verify_user_token(token[:-2] + "xx")


def test_jwt_rejects_unsigned_alg_none_token():
    """Verify jwt rejects unsigned alg none token."""
    unsigned = jwt.encode(
        {"sub": str(uuid.uuid4()), "aud": "genchat:user", "iat": 1, "exp": 9999999999},
        key="",
        algorithm="none",
    )

    with pytest.raises(InvalidCredentialError):
        _tokens().verify_user_token(unsigned)


def test_jwt_rejects_non_uuid_subject():
    """Verify jwt rejects non uuid subject."""
    token = jwt.encode(
        {"sub": "not-a-uuid", "aud": "genchat:user", "iat": 1, "exp": 9999999999},
        SECRET,
        algorithm="HS256",
    )

    with pytest.raises(InvalidCredentialError):
        _tokens().verify_user_token(token)


# --- GoogleTokenVerifierAdapter -------------------------------------------------------

_VERIFY = "app.infrastructure.auth.google_token_verifier_adapter.id_token.verify_oauth2_token"


def test_google_adapter_maps_payload_to_profile():
    """Verify google adapter maps payload to profile."""
    payload = {
        "iss": "https://accounts.google.com",
        "sub": "s1",
        "email": " Ada@Example.COM ",
        "email_verified": True,
        "name": "Ada L",
    }
    with patch(_VERIFY, return_value=payload) as verify:
        profile = GoogleTokenVerifierAdapter("client-id").verify("cred")

    assert profile == GoogleProfile("s1", "ada@example.com", True, "Ada L")
    assert verify.call_args.args[2] == "client-id"


def test_google_adapter_falls_back_to_email_local_part_for_name():
    """Verify google adapter falls back to email local part for name."""
    payload = {
        "iss": "accounts.google.com",
        "sub": "s1",
        "email": "ada@example.com",
        "email_verified": True,
    }
    with patch(_VERIFY, return_value=payload):
        profile = GoogleTokenVerifierAdapter("client-id").verify("cred")

    assert profile.name == "ada"


@pytest.mark.parametrize("error", [ValueError("Wrong recipient"), GoogleAuthError("boom")])
def test_google_adapter_maps_library_errors_to_domain_error(error):
    """Verify google adapter maps library errors to domain error."""
    with patch(_VERIFY, side_effect=error):
        with pytest.raises(InvalidCredentialError):
            GoogleTokenVerifierAdapter("client-id").verify("cred")


@pytest.mark.parametrize(
    "payload",
    [
        {"iss": "https://accounts.google.com", "email": "a@b.co"},
        {"iss": "https://accounts.google.com", "sub": "s1"},
        {"iss": "https://accounts.google.com"},
        {"iss": "https://evil.example.com", "sub": "s1", "email": "a@b.co"},
        {"sub": "s1", "email": "a@b.co"},
    ],
)
def test_google_adapter_requires_issuer_sub_and_email(payload):
    """Verify google adapter requires valid issuer, sub and email."""
    with patch(_VERIFY, return_value=payload):
        with pytest.raises(InvalidCredentialError):
            GoogleTokenVerifierAdapter("client-id").verify("cred")


def test_google_adapter_treats_missing_email_verified_as_unverified():
    """Verify google adapter treats missing email verified as unverified."""
    payload = {
        "iss": "https://accounts.google.com",
        "sub": "s1",
        "email": "a@b.co",
        "email_verified": "true",
    }
    with patch(_VERIFY, return_value=payload):
        profile = GoogleTokenVerifierAdapter("client-id").verify("cred")

    assert not profile.email_verified
