"""Use cases for uploading, downloading, presigning, and deleting bucket objects."""

from typing import BinaryIO
from app.domain.entities.object_item import (
    MAX_UPLOAD_SIZE_BYTES,
    ObjectContent,
    PresignedDownload,
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


class GetPresignedUrlUseCase:  # pylint: disable=too-few-public-methods
    """Generate a short-lived presigned download URL for a stored object."""

    def __init__(self, storage: ObjectStoragePort):
        self._storage = storage

    def execute(self, object_key: str) -> PresignedDownload:
        """Sanitize object_key and return a PresignedDownload value object."""
        clean_key = sanitize_filename(object_key)
        return self._storage.create_presigned_download(clean_key)


class DownloadObjectBytesUseCase:  # pylint: disable=too-few-public-methods
    """Fetch raw bytes of a stored object for internal service processing."""

    def __init__(self, storage: ObjectStoragePort):
        self._storage = storage

    def execute(self, object_key: str) -> ObjectContent:
        """Sanitize object_key and return an ObjectContent value object."""
        clean_key = sanitize_filename(object_key)
        raw_bytes = self._storage.get_object_bytes(clean_key)
        return ObjectContent(object_key=clean_key, content=raw_bytes)


class DeleteObjectUseCase:  # pylint: disable=too-few-public-methods
    """Delete a stored object from the bucket."""

    def __init__(self, storage: ObjectStoragePort):
        self._storage = storage

    def execute(self, object_key: str) -> None:
        """Sanitize object_key and remove it from the bucket."""
        clean_key = sanitize_filename(object_key)
        self._storage.delete_object(clean_key)
