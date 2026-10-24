"""Port defining document processing operations."""

from abc import ABC, abstractmethod
from app.domain.entities.file import StoredFile


class DocumentProcessorPort(ABC):
    """Port for document processing operations."""

    @abstractmethod
    def convert_docx_to_pdf(self, filename: str) -> StoredFile:
        """Converts DOCX to PDF, stores the result, and returns StoredFile."""

    @abstractmethod
    def convert_pdf_to_docx(self, filename: str) -> StoredFile:
        """Converts PDF to DOCX, stores the result, and returns StoredFile."""
