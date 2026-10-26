"""Use case for deleting a stored object."""

from app.domain.entities.object_item import sanitize_filename
from app.application.ports.object_storage_port import ObjectStoragePort


class DeleteObjectUseCase:  # pylint: disable=too-few-public-methods
    """Delete a stored object from the bucket."""

    def __init__(self, storage: ObjectStoragePort):
        self._storage = storage

    def execute(self, object_key: str) -> None:
        """Sanitize object_key and remove it from the bucket."""
        clean_key = sanitize_filename(object_key)
        self._storage.delete_object(clean_key)
