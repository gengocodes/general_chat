"""Use case for fetching raw object bytes for internal service processing."""

from app.domain.entities.object_item import ObjectContent, sanitize_filename
from app.application.ports.object_storage_port import ObjectStoragePort


class DownloadObjectBytesUseCase:  # pylint: disable=too-few-public-methods
    """Fetch raw bytes of a stored object for internal service processing."""

    def __init__(self, storage: ObjectStoragePort):
        self._storage = storage

    def execute(self, object_key: str) -> ObjectContent:
        """Sanitize object_key and return an ObjectContent value object."""
        clean_key = sanitize_filename(object_key)
        raw_bytes = self._storage.get_object_bytes(clean_key)
        return ObjectContent(object_key=clean_key, content=raw_bytes)
