"""
Domain entities, value objects, and validation rules for R2 object storage.
"""

from dataclasses import dataclass
from datetime import datetime
import posixpath
import uuid
from app.domain.errors import InvalidObjectError


MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
ALLOWED_OBJECT_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx"})


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an untrusted filename by stripping directory components and whitespace,
    and enforcing the allowed object extension whitelist (.pdf and .docx).
    Raises InvalidObjectError if the filename is empty, invalid, or has an unsupported extension.
    """
    normalized = filename.replace("\\", "/")
    clean_name = posixpath.basename(normalized).strip()
    if not clean_name or clean_name in {".", ".."}:
        raise InvalidObjectError("Filename cannot be empty or invalid.")
    _, extension = posixpath.splitext(clean_name)
    if extension.lower() not in ALLOWED_OBJECT_EXTENSIONS:
        raise InvalidObjectError("Only .pdf and .docx files are supported.")
    return clean_name


def generate_object_key(clean_filename: str) -> str:
    """Generate a collision-free, non-guessable object key using a UUID prefix."""
    return f"{uuid.uuid4().hex[:12]}_{clean_filename}"


@dataclass(frozen=True)
class StoredObject:
    """Value object representing an uploaded object in Cloudflare R2."""

    object_key: str
    original_name: str
    size_bytes: int
    download_url: str
    expires_at: datetime


@dataclass(frozen=True)
class PresignedDownload:
    """Value object representing a presigned download URL for an existing object."""

    object_key: str
    download_url: str
    expires_in_seconds: int


@dataclass(frozen=True)
class ObjectContent:
    """Value object representing raw object bytes retrieved from the bucket."""

    object_key: str
    content: bytes
