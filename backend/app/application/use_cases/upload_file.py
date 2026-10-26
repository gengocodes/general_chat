"""Use case for handling file uploads."""

from typing import BinaryIO
from app.domain.entities.file import StoredFile, sanitize_filename
from app.application.ports.file_storage_port import FileStoragePort


class UploadFileUseCase:  # pylint: disable=too-few-public-methods
    """Use case for handling file uploads."""

    def __init__(self, storage: FileStoragePort):
        self._storage = storage

    def execute(
        self, original_name: str, file_obj: BinaryIO
    ) -> StoredFile:
        """
        Validates and saves uploaded file via storage port.
        Returns StoredFile domain value object.
        """
        sanitize_filename(original_name)
        return self._storage.save_file(original_name, file_obj)
