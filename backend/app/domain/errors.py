"""
Domain exceptions for GenChat.
"""


class DomainError(Exception):
    """Base domain exception."""


class AgentServiceError(DomainError):
    """Raised when agent operations fail."""


class FileNotFoundDomainError(DomainError):
    """Raised when a requested file does not exist in storage."""


class FileSizeLimitExceededError(DomainError):
    """Raised when an uploaded file exceeds the maximum allowed byte size."""


class InvalidFileError(DomainError):
    """Raised when an uploaded file has an invalid name or format."""


class DocumentConversionError(DomainError):
    """Raised when document conversion fails."""
