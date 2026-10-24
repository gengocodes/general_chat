"""Port defining cloud bucket object storage operations."""

from abc import ABC, abstractmethod
from app.domain.entities.object_item import PresignedDownload, StoredObject


class ObjectStoragePort(ABC):
    """Abstract outbound port for interacting with an S3/R2 object bucket."""

    @abstractmethod
    def put_object(
        self,
        object_key: str,
        original_name: str,
        content: bytes,
        content_type: str,
    ) -> StoredObject:
        """Upload object bytes to the bucket and return a StoredObject with presigned URL."""

    @abstractmethod
    def create_presigned_download(self, object_key: str) -> PresignedDownload:
        """Generate a short-lived presigned download URL for an existing object key."""

    @abstractmethod
    def get_object_bytes(self, object_key: str) -> bytes:
        """Fetch raw object bytes from the bucket. Raises ObjectNotFoundError if absent."""

    @abstractmethod
    def delete_object(self, object_key: str) -> None:
        """Delete an object from the bucket."""
