"""Port defining storage operations for uploaded files."""

from abc import ABC, abstractmethod
from typing import BinaryIO
from app.domain.entities.file import StoredFile, FileDownload


class FileStoragePort(ABC):
    """Port for file storage operations."""

    @abstractmethod
    def save_file(self, filename: str, file_obj: BinaryIO) -> StoredFile:
        """
        Saves file content to storage and returns a StoredFile value object.
        Raises InvalidFileError or FileSizeLimitExceededError on validation failure.
        """

    @abstractmethod
    def resolve_download(self, filename: str) -> FileDownload:
        """
        Resolves a stored file for download.
        Raises FileNotFoundDomainError if the file does not exist.
        """
