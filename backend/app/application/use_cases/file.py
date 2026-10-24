"""Use cases for file uploads and downloads."""

from typing import BinaryIO
from app.domain.entities.file import StoredFile, FileDownload, sanitize_filename
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


class GetFileDownloadUseCase:  # pylint: disable=too-few-public-methods
    """Use case for verifying and resolving file downloads."""

    def __init__(self, storage: FileStoragePort):
        self._storage = storage

    def execute(self, filename: str) -> FileDownload:
        """
        Resolves download information for a file.
        Returns FileDownload domain value object.
        Raises FileNotFoundDomainError if file is not in storage.
        """
        clean_filename = sanitize_filename(filename)
        return self._storage.resolve_download(clean_filename)
