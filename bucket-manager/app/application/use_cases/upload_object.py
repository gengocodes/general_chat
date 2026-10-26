"""Use case for validating, key-prefixing, and uploading bucket objects."""

from typing import BinaryIO
from app.domain.entities.object_item import (
    MAX_UPLOAD_SIZE_BYTES,
    StoredObject,
    generate_object_key,
    sanitize_filename,
)
from app.domain.errors import ObjectSizeLimitExceededError
from app.application.ports.object_storage_port import ObjectStoragePort

STREAM_CHUNK_SIZE: int = 64 * 1024  # 64 KB


def read_bounded_stream(
    file_obj: BinaryIO,
    max_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> bytes:
    """Read a binary stream in chunks and raise ObjectSizeLimitExceededError if over max_bytes."""
    chunks: list[bytes] = []
    total_bytes = 0
    while True:
        chunk = file_obj.read(STREAM_CHUNK_SIZE)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise ObjectSizeLimitExceededError(
                f"File exceeds maximum allowed size of {max_bytes} bytes."
            )
        chunks.append(chunk)
    return b"".join(chunks)


class UploadObjectUseCase:  # pylint: disable=too-few-public-methods
    """Validate, key-prefix, and upload an object stream to storage."""

    def __init__(
        self,
        storage: ObjectStoragePort,
        max_upload_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    ):
        self._storage = storage
        self._max_upload_bytes = max_upload_bytes

    def execute(
        self,
        original_name: str,
        file_obj: BinaryIO,
        content_type: str = "application/octet-stream",
    ) -> StoredObject:
        """Sanitize filename, read bounded bytes, and store in bucket with UUID prefix."""
        clean_filename = sanitize_filename(original_name)
        content = read_bounded_stream(file_obj, self._max_upload_bytes)
        object_key = generate_object_key(clean_filename)
        return self._storage.put_object(
            object_key=object_key,
            original_name=clean_filename,
            content=content,
            content_type=content_type,
        )
