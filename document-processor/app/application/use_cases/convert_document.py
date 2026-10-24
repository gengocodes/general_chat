"""Use cases for document format conversion."""

from app.domain.entities.conversion import (
    ConvertedDocument,
    TargetFormat,
    sanitize_filename,
)
from app.domain.errors import InvalidDocumentError
from app.application.ports.document_converter_port import DocumentConverterPort


class ConvertDocumentUseCase:  # pylint: disable=too-few-public-methods
    """Use case orchestrating DOCX-to-PDF and PDF-to-DOCX document conversion."""

    def __init__(self, converter: DocumentConverterPort):
        self._converter = converter

    def execute(self, filename: str, target_format: TargetFormat) -> ConvertedDocument:
        """Validate filename and target format and invoke the appropriate converter method."""
        clean_name = sanitize_filename(filename)
        if target_format == "pdf":
            return self._converter.convert_docx_to_pdf(clean_name)
        if target_format == "docx":
            return self._converter.convert_pdf_to_docx(clean_name)
        raise InvalidDocumentError(f"Unsupported target format: '{target_format}'.")
