"""Use case for generating presigned download URLs."""

from app.domain.entities.object_item import PresignedDownload, sanitize_filename
from app.application.ports.object_storage_port import ObjectStoragePort


class GetPresignedUrlUseCase:  # pylint: disable=too-few-public-methods
    """Generate a short-lived presigned download URL for a stored object."""

    def __init__(self, storage: ObjectStoragePort):
        self._storage = storage

    def execute(self, object_key: str) -> PresignedDownload:
        """Sanitize object_key and return a PresignedDownload value object."""
        clean_key = sanitize_filename(object_key)
        return self._storage.create_presigned_download(clean_key)
