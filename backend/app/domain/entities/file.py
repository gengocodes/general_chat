"""
Domain entities, value objects, and validation rules for stored files and downloads.
"""

from dataclasses import dataclass
import posixpath
from app.domain.errors import InvalidFileError


MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx"})


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an untrusted filename by stripping directory components and whitespace,
    and enforcing the allowed file extension whitelist (.pdf and .docx).
    Raises InvalidFileError if the filename is empty, invalid, or has an unsupported extension.
    """
    normalized = filename.replace("\\", "/")
    clean_name = posixpath.basename(normalized).strip()
    if not clean_name or clean_name in {".", ".."}:
        raise InvalidFileError("Filename cannot be empty or invalid.")
    _, extension = posixpath.splitext(clean_name)
    if extension.lower() not in ALLOWED_FILE_EXTENSIONS:
        raise InvalidFileError("Only .pdf and .docx files are supported.")
    return clean_name


@dataclass(frozen=True)
class StoredFile:
    """Value object representing a saved file in storage."""

    filename: str
    original_name: str
    size_bytes: int
    download_url: str


@dataclass(frozen=True)
class FileDownload:
    """Value object representing a resolved presigned download URL for a file."""

    filename: str
    download_url: str
