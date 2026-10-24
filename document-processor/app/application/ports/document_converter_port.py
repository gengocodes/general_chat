"""Outbound port defining document conversion and storage operations."""

from abc import ABC, abstractmethod
from app.domain.entities.conversion import ConvertedDocument


class DocumentConverterPort(ABC):
    """Port for converting stored documents between DOCX and PDF formats."""

    @abstractmethod
    def convert_docx_to_pdf(self, filename: str) -> ConvertedDocument:
        """
        Fetch source DOCX from storage, convert to PDF, upload output to storage,
        and return a ConvertedDocument value object.
        """

    @abstractmethod
    def convert_pdf_to_docx(self, filename: str) -> ConvertedDocument:
        """
        Fetch source PDF from storage, convert to DOCX, upload output to storage,
        and return a ConvertedDocument value object.
        """
