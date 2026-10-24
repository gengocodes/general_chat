"""
Domain entities, value objects, and validation rules for stored files and downloads.
"""

from dataclasses import dataclass
import posixpath
import re
from app.domain.errors import InvalidFileError


MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
_UUID_PREFIX_PATTERN = re.compile(r"^[0-9a-fA-F]{12}_")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an untrusted filename by stripping directory components and whitespace.
    Raises InvalidFileError if the resulting filename is empty or a dot-segment.
    """
    normalized = filename.replace("\\", "/")
    clean_name = posixpath.basename(normalized).strip()
    if not clean_name or clean_name in {".", ".."}:
        raise InvalidFileError("Filename cannot be empty or invalid.")
    return clean_name


def extract_original_base_name(object_key_or_filename: str) -> str:
    """
    Extract the clean base filename without extensions and strip any 12-hex UUID prefix.
    Example: 'a1b2c3d4e5f6_report.docx' -> 'report'
    """
    clean_name = sanitize_filename(object_key_or_filename)
    base_name, _ = posixpath.splitext(clean_name)
    return _UUID_PREFIX_PATTERN.sub("", base_name)


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
