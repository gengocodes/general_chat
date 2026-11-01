"""
Composition Root: Dependency wiring for FastAPI
"""

from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.application.ports.google_token_verifier_port import GoogleTokenVerifierPort
from app.application.ports.guest_usage_port import GuestUsagePort
from app.application.ports.session_token_port import SessionTokenPort
from app.application.ports.user_repository_port import UserRepositoryPort
from app.application.use_cases.chat import StreamChatMessageUseCase
from app.application.use_cases.chat_access import ChatAccessUseCase
from app.application.use_cases.get_session import GetSessionUseCase
from app.application.use_cases.google_login import GoogleLoginUseCase
from app.application.use_cases.resolve_principal import ResolvePrincipalUseCase
from app.application.use_cases.upload_file import UploadFileUseCase
from app.application.use_cases.get_file_download import GetFileDownloadUseCase
from app.domain.entities.principal import ResolvedPrincipal
from app.domain.errors import LoginRequiredError, PersistenceError
from app.infrastructure.auth.google_token_verifier_adapter import (
    GoogleTokenVerifierAdapter,
)
from app.infrastructure.auth.jwt_session_adapter import JwtSessionAdapter
from app.infrastructure.cloud_run_auth import build_service_auth
from app.infrastructure.persistence.database import create_session_factory
from app.infrastructure.persistence.guest_usage_repository import (
    SqlAlchemyGuestUsageRepository,
)
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.storage.bucket_manager_adapter import (
    BucketManagerStorageAdapter,
)
from app.infrastructure.document.document_processor_adapter import (
    DocumentProcessorHttpAdapter,
)
from app.infrastructure.llm.document_tools import (
    DOCUMENT_TOOL_ACTIVITY_LABELS,
    create_document_tools,
)
from app.infrastructure.llm.langchain_adapter import LangChainChatAdapter
from app.presentation.cookies import read_guest_token, read_session_token
from app.presentation.rate_limit import SlidingWindowRateLimiter

# Singletons / reusable infrastructure instances
_session_factory = create_session_factory(settings.DATABASE_URL)
_user_repository = SqlAlchemyUserRepository(_session_factory)
_guest_usage_repository = SqlAlchemyGuestUsageRepository(_session_factory)
_session_tokens = JwtSessionAdapter(
    secret=settings.JWT_SECRET,
    user_lifetime=timedelta(days=settings.SESSION_LIFETIME_DAYS),
)
_google_verifier = GoogleTokenVerifierAdapter(client_id=settings.GOOGLE_CLIENT_ID)

_storage_adapter = BucketManagerStorageAdapter(
    base_url=settings.BUCKET_MANAGER_URL,
    internal_api_key=settings.INTERNAL_API_KEY,
    auth=build_service_auth(
        settings.BUCKET_MANAGER_URL, settings.INTERNAL_IAM_AUTH_ENABLED
    ),
)
_document_processor = DocumentProcessorHttpAdapter(
    base_url=settings.DOCUMENT_PROCESSOR_URL,
    internal_api_key=settings.INTERNAL_API_KEY,
    auth=build_service_auth(
        settings.DOCUMENT_PROCESSOR_URL, settings.INTERNAL_IAM_AUTH_ENABLED
    ),
)
_document_tools = create_document_tools(document_processor=_document_processor)

chat_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.CHAT_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)
auth_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.AUTH_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)
upload_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.UPLOAD_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)
download_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.DOWNLOAD_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)


def get_chat_model_adapter() -> LangChainChatAdapter:
    """Creates LangChainChatAdapter bound to Google Gemini model and tools."""
    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )
    return LangChainChatAdapter(
        model=model,
        tools=_document_tools,
        activity_labels=DOCUMENT_TOOL_ACTIVITY_LABELS,
    )


def get_stream_chat_use_case() -> StreamChatMessageUseCase:
    """Provides StreamChatMessageUseCase wired with ChatModelPort adapter."""
    chat_model = get_chat_model_adapter()
    return StreamChatMessageUseCase(chat_model=chat_model)


def get_upload_file_use_case() -> UploadFileUseCase:
    """Provides UploadFileUseCase wired with FileStoragePort adapter."""
    return UploadFileUseCase(storage=_storage_adapter)


def get_file_download_use_case() -> GetFileDownloadUseCase:
    """Provides GetFileDownloadUseCase wired with FileStoragePort adapter."""
    return GetFileDownloadUseCase(storage=_storage_adapter)


def get_user_repository() -> UserRepositoryPort:
    """Provides the UserRepositoryPort adapter."""
    return _user_repository


def get_guest_usage_repository() -> GuestUsagePort:
    """Provides the GuestUsagePort adapter."""
    return _guest_usage_repository


def get_session_tokens() -> SessionTokenPort:
    """Provides the SessionTokenPort adapter."""
    return _session_tokens


def get_google_verifier() -> GoogleTokenVerifierPort:
    """Provides the GoogleTokenVerifierPort adapter."""
    return _google_verifier


def get_google_login_use_case(
    verifier: GoogleTokenVerifierPort = Depends(get_google_verifier),
    users: UserRepositoryPort = Depends(get_user_repository),
    tokens: SessionTokenPort = Depends(get_session_tokens),
) -> GoogleLoginUseCase:
    """Provides GoogleLoginUseCase wired with Google, user and token adapters."""
    return GoogleLoginUseCase(verifier=verifier, users=users, tokens=tokens)


def get_resolve_principal_use_case(
    tokens: SessionTokenPort = Depends(get_session_tokens),
) -> ResolvePrincipalUseCase:
    """Provides ResolvePrincipalUseCase wired with the session token adapter."""
    return ResolvePrincipalUseCase(tokens=tokens)


def get_chat_access_use_case(
    guests: GuestUsagePort = Depends(get_guest_usage_repository),
) -> ChatAccessUseCase:
    """Provides ChatAccessUseCase wired with the guest usage repository."""
    return ChatAccessUseCase(
        guests=guests,
        free_message_limit=settings.FREE_MESSAGE_LIMIT,
    )


def get_session_use_case(
    users: UserRepositoryPort = Depends(get_user_repository),
    access: ChatAccessUseCase = Depends(get_chat_access_use_case),
) -> GetSessionUseCase:
    """Provides GetSessionUseCase wired with the user repository and access policy."""
    return GetSessionUseCase(users=users, access=access)


def verify_request_origin(request: Request) -> None:
    """CSRF defense for cookie-authenticated writes: reject requests from foreign origins.

    Browsers send Origin on cross-site POSTs; if Origin is omitted, fall back to the
    origin of Referer. Non-browser clients that omit both are not a CSRF vector.
    """
    origin = request.headers.get("Origin")
    if origin is not None:
        if origin not in settings.cors_origins:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request origin is not allowed.",
            )
        return
    referer = request.headers.get("Referer")
    if referer is not None and not any(
        referer == allowed or referer.startswith(f"{allowed}/")
        for allowed in settings.cors_origins
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed.",
        )


def get_resolved_principal(
    request: Request,
    use_case: ResolvePrincipalUseCase = Depends(get_resolve_principal_use_case),
) -> ResolvedPrincipal:
    """Resolve the request identity from its cookies (minting a guest when absent)."""
    return use_case.execute(read_session_token(request), read_guest_token(request))


def _login_required_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "login_required",
            "message": "You have used your free messages. Sign in with Google to continue.",
        },
    )


def _usage_unavailable_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Usage tracking is temporarily unavailable.",
    )


def consume_free_message(
    resolved: ResolvedPrincipal, access: ChatAccessUseCase
) -> None:
    """Consume one free message for guests; reject with 401 login_required when exhausted.

    Called from the handler (not as a FastAPI dependency) so that requests failing body
    validation never consume a free message. It performs blocking database I/O.
    """
    try:
        access.consume_message(resolved.principal)
    except LoginRequiredError as exc:
        raise _login_required_error() from exc
    except PersistenceError as exc:
        raise _usage_unavailable_error() from exc


def require_upload_access(
    resolved: ResolvedPrincipal = Depends(get_resolved_principal),
    access: ChatAccessUseCase = Depends(get_chat_access_use_case),
) -> ResolvedPrincipal:
    """Block uploads from guests that have no free messages left (does not consume one)."""
    try:
        access.ensure_access(resolved.principal)
    except LoginRequiredError as exc:
        raise _login_required_error() from exc
    except PersistenceError as exc:
        raise _usage_unavailable_error() from exc
    return resolved
