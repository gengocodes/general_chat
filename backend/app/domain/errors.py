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


class InvalidCredentialError(DomainError):
    """Raised when a Google ID token or session/guest token is invalid or expired."""


class UnverifiedEmailError(DomainError):
    """Raised when the Google account email address is not verified."""


class LoginRequiredError(DomainError):
    """Raised when a guest has used all free messages and must sign in."""


class PersistenceError(DomainError):
    """Raised when the database cannot complete an operation."""
