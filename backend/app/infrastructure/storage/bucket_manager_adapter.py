"""HTTP storage adapter communicating with the standalone bucket-manager microservice."""

import io
import logging
from typing import BinaryIO
import httpx

from app.domain.entities.file import (
    MAX_UPLOAD_SIZE_BYTES,
    FileDownload,
    StoredFile,
    sanitize_filename,
)
from app.domain.errors import (
    DomainError,
    FileNotFoundDomainError,
    FileSizeLimitExceededError,
    InvalidFileError,
)
from app.application.ports.file_storage_port import FileStoragePort

logger = logging.getLogger(__name__)

STREAM_CHUNK_SIZE: int = 64 * 1024  # 64 KB


def _read_bounded_bytes(file_obj: BinaryIO, max_upload_bytes: int) -> bytes:
    """Read a stream in chunks and raise FileSizeLimitExceededError if over max_upload_bytes."""
    chunks: list[bytes] = []
    size_bytes = 0
    while True:
        chunk = file_obj.read(STREAM_CHUNK_SIZE)
        if not chunk:
            break
        size_bytes += len(chunk)
        if size_bytes > max_upload_bytes:
            raise FileSizeLimitExceededError(
                f"File exceeds maximum allowed size of {max_upload_bytes} bytes."
            )
        chunks.append(chunk)
    return b"".join(chunks)


class BucketManagerStorageAdapter(FileStoragePort):
    """FileStoragePort implementation delegating object storage to bucket-manager."""

    def __init__(
        self,
        base_url: str,
        internal_api_key: str,
        max_upload_bytes: int = MAX_UPLOAD_SIZE_BYTES,
        timeout_seconds: float = 30.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-Internal-API-Key": internal_api_key}
        self._max_upload_bytes = max_upload_bytes
        self._timeout = timeout_seconds

    def save_file(self, filename: str, file_obj: BinaryIO) -> StoredFile:
        clean_filename = sanitize_filename(filename)
        payload_bytes = _read_bounded_bytes(file_obj, self._max_upload_bytes)

        try:
            response = httpx.post(
                f"{self._base_url}/api/objects/upload",
                headers=self._headers,
                files={
                    "file": (
                        clean_filename,
                        io.BytesIO(payload_bytes),
                        "application/octet-stream",
                    )
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.exception("Bucket-manager upload request failed: %s", str(exc))
            raise DomainError("Could not communicate with storage service.") from exc

        if response.status_code == 400:
            raise InvalidFileError("Invalid or empty filename.")
        if response.status_code == 413:
            raise FileSizeLimitExceededError(
                f"File exceeds maximum allowed size of {self._max_upload_bytes} bytes."
            )
        if not response.is_success:
            logger.error(
                "Bucket-manager returned %d on upload: %s",
                response.status_code,
                response.text,
            )
            raise DomainError("Storage service failed to save file.")

        data = response.json()
        return StoredFile(
            filename=data["object_key"],
            original_name=data["original_name"],
            size_bytes=data["size_bytes"],
            download_url=data["download_url"],
        )

    def resolve_download(self, filename: str) -> FileDownload:
        clean_filename = sanitize_filename(filename)
        try:
            response = httpx.get(
                f"{self._base_url}/api/objects/{clean_filename}/presigned",
                headers=self._headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.exception("Bucket-manager presigned URL request failed: %s", str(exc))
            raise DomainError("Could not communicate with storage service.") from exc

        if response.status_code == 404:
            raise FileNotFoundDomainError(f"File '{clean_filename}' does not exist.")
        if not response.is_success:
            raise DomainError("Storage service failed to resolve download URL.")

        data = response.json()
        return FileDownload(
            filename=data["object_key"],
            download_url=data["download_url"],
        )
