"""Composition Root and internal API key authentication for Document-Processor."""

from functools import lru_cache
import secrets
from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.application.ports.document_converter_port import DocumentConverterPort
from app.application.use_cases.convert_document import ConvertDocumentUseCase
from app.infrastructure.cloud_run_auth import build_service_auth
from app.infrastructure.converter.document_converter_adapter import (
    DocumentConverterAdapter,
)


def verify_internal_api_key(
    x_internal_api_key: str = Header(..., alias="X-Internal-API-Key"),
) -> None:
    """Verify the shared internal API key header using constant-time comparison."""
    if not secrets.compare_digest(x_internal_api_key, settings.INTERNAL_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key.",
        )


@lru_cache(maxsize=1)
def get_converter_adapter() -> DocumentConverterPort:
    """Provide singleton DocumentConverterAdapter configured with bucket-manager settings."""
    return DocumentConverterAdapter(
        bucket_manager_url=settings.BUCKET_MANAGER_URL,
        internal_api_key=settings.INTERNAL_API_KEY,
        auth=build_service_auth(
            settings.BUCKET_MANAGER_URL, settings.INTERNAL_IAM_AUTH_ENABLED
        ),
    )


def get_convert_document_use_case(
    converter: DocumentConverterPort = Depends(get_converter_adapter),
) -> ConvertDocumentUseCase:
    """Provide ConvertDocumentUseCase wired with DocumentConverterPort."""
    return ConvertDocumentUseCase(converter=converter)
