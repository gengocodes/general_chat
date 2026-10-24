"""HTTP document processor adapter communicating with the standalone document-processor service."""

import logging
from typing import Literal
import httpx

from app.domain.entities.file import StoredFile, sanitize_filename
from app.domain.errors import (
    DocumentConversionError,
    FileNotFoundDomainError,
    InvalidFileError,
)
from app.application.ports.document_processor_port import DocumentProcessorPort

logger = logging.getLogger(__name__)


class DocumentProcessorHttpAdapter(DocumentProcessorPort):
    """DocumentProcessorPort implementation delegating conversions to document-processor."""

    def __init__(
        self,
        base_url: str,
        internal_api_key: str,
        auth: httpx.Auth,
        timeout_seconds: float = 120.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-Internal-API-Key": internal_api_key}
        self._auth = auth
        self._timeout = timeout_seconds

    def _request_conversion(
        self, filename: str, target_format: Literal["pdf", "docx"]
    ) -> StoredFile:
        clean_filename = sanitize_filename(filename)
        try:
            response = httpx.post(
                f"{self._base_url}/api/documents/convert",
                headers=self._headers,
                auth=self._auth,
                json={"filename": clean_filename, "target_format": target_format},
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.exception("Document-processor request failed: %s", str(exc))
            raise DocumentConversionError(
                "Could not communicate with document-processor service."
            ) from exc

        if response.status_code == 400:
            raise InvalidFileError("Invalid filename or conversion format.")
        if response.status_code == 404:
            raise FileNotFoundDomainError(f"Source file '{clean_filename}' does not exist.")
        if not response.is_success:
            logger.error(
                "Document-processor returned %d: %s",
                response.status_code,
                response.text,
            )
            raise DocumentConversionError(
                f"Document conversion to {target_format.upper()} failed."
            )

        data = response.json()
        return StoredFile(
            filename=data["converted_filename"],
            original_name=data["original_name"],
            size_bytes=data["size_bytes"],
            download_url=data["download_url"],
        )

    def convert_docx_to_pdf(self, filename: str) -> StoredFile:
        return self._request_conversion(filename, "pdf")

    def convert_pdf_to_docx(self, filename: str) -> StoredFile:
        return self._request_conversion(filename, "docx")
