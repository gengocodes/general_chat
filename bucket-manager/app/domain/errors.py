"""
Domain exceptions for Bucket-Manager.
"""


class DomainError(Exception):
    """Base domain exception."""


class ObjectNotFoundError(DomainError):
    """Raised when a requested object key does not exist in the bucket."""


class ObjectSizeLimitExceededError(DomainError):
    """Raised when an uploaded object exceeds MAX_UPLOAD_SIZE_BYTES."""


class InvalidObjectError(DomainError):
    """Raised when an object key or filename is empty or invalid."""


class StorageProviderError(DomainError):
    """Raised when the underlying cloud object storage provider fails."""
