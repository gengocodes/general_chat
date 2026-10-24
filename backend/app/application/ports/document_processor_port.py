"""Port defining document processing operations."""

from abc import ABC, abstractmethod


class DocumentProcessorPort(ABC):
    """Port for document processing operations."""

    @abstractmethod
    def convert_docx_to_pdf(self, filename: str) -> str:
        """Converts DOCX to PDF and returns the output filename."""

    @abstractmethod
    def convert_pdf_to_docx(self, filename: str) -> str:
        """Converts PDF to DOCX and returns the output filename."""
