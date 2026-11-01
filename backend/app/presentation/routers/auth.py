"""Authentication endpoints: Google sign-in, session state and logout."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.use_cases.get_session import GetSessionUseCase
from app.application.use_cases.google_login import GoogleLoginUseCase
from app.domain.entities.principal import ResolvedPrincipal
from app.domain.entities.user import AuthenticatedUser
from app.domain.errors import (
    InvalidCredentialError,
    PersistenceError,
    UnverifiedEmailError,
)
from app.presentation.cookies import (
    clear_session_cookie,
    set_guest_cookie,
    set_session_cookie,
)
from app.presentation.dependencies import (
    auth_rate_limiter,
    get_google_login_use_case,
    get_resolved_principal,
    get_session_use_case,
    verify_request_origin,
)
from app.presentation.schemas.auth import (
    GoogleLoginRequest,
    SessionResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
    dependencies=[Depends(auth_rate_limiter)],
)


def _to_user_response(user: AuthenticatedUser) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, name=user.name)


@router.post(
    "/google",
    response_model=UserResponse,
    dependencies=[Depends(verify_request_origin)],
)
def google_login(
    body: GoogleLoginRequest,
    response: Response,
    use_case: GoogleLoginUseCase = Depends(get_google_login_use_case),
) -> UserResponse:
    """Exchange a Google ID token for a signed-in session cookie."""
    try:
        result = use_case.execute(body.credential)
    except InvalidCredentialError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential.",
        ) from exc
    except UnverifiedEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email is not verified.",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sign-in is temporarily unavailable.",
        ) from exc
    set_session_cookie(response, result.session_token)
    return _to_user_response(result.user)


@router.get("/session", response_model=SessionResponse)
def get_session(
    response: Response,
    resolved: ResolvedPrincipal = Depends(get_resolved_principal),
    use_case: GetSessionUseCase = Depends(get_session_use_case),
) -> SessionResponse:
    """Return the signed-in user or whether the guest must sign in."""
    if resolved.new_guest_token is not None:
        set_guest_cookie(response, resolved.new_guest_token)
    try:
        state = use_case.execute(resolved.principal)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session lookup is temporarily unavailable.",
        ) from exc
    user = None if state.user is None else _to_user_response(state.user)
    return SessionResponse(user=user, login_required=state.login_required)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_request_origin)],
)
def logout() -> Response:
    """Clear the session cookie. The guest identity (and its used quota) is kept."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response)
    return response
