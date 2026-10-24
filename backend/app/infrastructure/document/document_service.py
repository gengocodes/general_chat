"""Local document processing implementation."""

from dataclasses import dataclass
import os
import logging
import importlib
from app.domain.entities.file import sanitize_filename
from app.domain.errors import (
    DocumentConversionError,
    FileNotFoundDomainError,
)
from app.application.ports.document_processor_port import DocumentProcessorPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversionPaths:
    """Resolved input and output filesystem paths for a document conversion."""

    input_path: str
    output_path: str
    output_filename: str


class LocalDocumentService(DocumentProcessorPort):
    """DocumentProcessorPort implementation for local document operations."""

    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = upload_dir

    def _prepare_conversion_paths(
        self, filename: str, target_ext: str
    ) -> ConversionPaths:
        """Validate input file existence and return resolved ConversionPaths."""
        clean_name = sanitize_filename(filename)
        input_path = os.path.join(self.upload_dir, clean_name)
        if not os.path.isfile(input_path):
            raise FileNotFoundDomainError(f"File '{filename}' does not exist.")

        base_name, _ = os.path.splitext(clean_name)
        output_filename = f"{base_name}.{target_ext}"
        output_path = os.path.join(self.upload_dir, output_filename)
        logger.info("Converting %s to %s", input_path, output_path)
        return ConversionPaths(
            input_path=input_path,
            output_path=output_path,
            output_filename=output_filename,
        )

    def convert_docx_to_pdf(self, filename: str) -> str:
        paths = self._prepare_conversion_paths(filename, "pdf")

        try:
            docx2pdf_module = importlib.import_module("docx2pdf")
            docx2pdf_module.convert(paths.input_path, paths.output_path)
        except ImportError as e:
            raise DocumentConversionError(
                "docx2pdf is required for DOCX to PDF conversion but is not installed."
            ) from e

        return paths.output_filename

    def convert_pdf_to_docx(self, filename: str) -> str:
        paths = self._prepare_conversion_paths(filename, "docx")

        try:
            pdf2docx_module = importlib.import_module("pdf2docx")
            cv = pdf2docx_module.Converter(paths.input_path)
            cv.convert(paths.output_path)
            cv.close()
        except ImportError as e:
            raise DocumentConversionError(
                "pdf2docx is required for PDF to DOCX conversion but is not installed."
            ) from e

        return paths.output_filename
