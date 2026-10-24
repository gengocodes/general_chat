"""Local disk storage adapter implementing FileStoragePort."""

import os
import logging
from typing import BinaryIO
from app.domain.entities.file import (
    MAX_UPLOAD_SIZE_BYTES,
    StoredFile,
    FileDownload,
    sanitize_filename,
)
from app.domain.errors import (
    FileNotFoundDomainError,
    FileSizeLimitExceededError,
)
from app.application.ports.file_storage_port import FileStoragePort

logger = logging.getLogger(__name__)

STREAM_CHUNK_SIZE: int = 64 * 1024  # 64 KB chunks


class LocalStorageAdapter(FileStoragePort):
    """FileStoragePort implementation using local disk storage."""

    def __init__(
        self,
        upload_dir: str = "./uploads",
        max_upload_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    ):
        self.upload_dir = upload_dir
        self.max_upload_bytes = max_upload_bytes
        os.makedirs(self.upload_dir, exist_ok=True)

    def _get_target_path(self, clean_filename: str) -> str:
        """Return target filesystem path inside the configured upload directory."""
        return os.path.join(self.upload_dir, clean_filename)

    def save_file(self, filename: str, file_obj: BinaryIO) -> StoredFile:
        clean_filename = sanitize_filename(filename)
        target_path = self._get_target_path(clean_filename)
        size_bytes = 0

        try:
            with open(target_path, "wb") as buffer:
                while True:
                    chunk = file_obj.read(STREAM_CHUNK_SIZE)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    if size_bytes > self.max_upload_bytes:
                        raise FileSizeLimitExceededError(
                            f"File exceeds maximum allowed size of {self.max_upload_bytes} bytes."
                        )
                    buffer.write(chunk)
        except Exception:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise

        logger.info("Uploaded file saved: %s (%d bytes)", target_path, size_bytes)
        return StoredFile(
            filename=clean_filename,
            original_name=filename,
            size_bytes=size_bytes,
            file_path=target_path,
        )

    def resolve_download(self, filename: str) -> FileDownload:
        clean_filename = sanitize_filename(filename)
        target_path = self._get_target_path(clean_filename)
        if not os.path.isfile(target_path):
            raise FileNotFoundDomainError(f"File '{clean_filename}' does not exist.")
        return FileDownload(filename=clean_filename, file_path=target_path)
