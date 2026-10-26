"""Use case for verifying and resolving file downloads."""

from app.domain.entities.file import FileDownload, sanitize_filename
from app.application.ports.file_storage_port import FileStoragePort


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
