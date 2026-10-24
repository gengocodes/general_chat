"""Domain exceptions for Document-Processor operations."""


class DomainError(Exception):
    """Base exception for all domain-level errors in Document-Processor."""


class SourceDocumentNotFoundError(DomainError):
    """Raised when the source document key does not exist in storage."""


class InvalidDocumentError(DomainError):
    """Raised when a filename or conversion target format is invalid."""


class DocumentConversionError(DomainError):
    """Raised when document format conversion fails."""


class StorageServiceError(DomainError):
    """Raised when communication with the bucket-manager storage service fails."""
