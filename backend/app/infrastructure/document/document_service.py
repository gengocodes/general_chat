"""Local document processing implementation."""

from dataclasses import dataclass
import importlib
import logging
import os
import shutil
import subprocess
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

    def _convert_docx_via_libreoffice(self, paths: ConversionPaths) -> bool:
        """Attempt DOCX to PDF conversion using headless LibreOffice if available."""
        soffice_bin = shutil.which("libreoffice") or shutil.which("soffice")
        if not soffice_bin:
            return False

        try:
            subprocess.run(
                [
                    soffice_bin,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    self.upload_dir,
                    paths.input_path,
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except (subprocess.SubprocessError, OSError) as e:
            raise DocumentConversionError(
                f"LibreOffice failed to convert '{paths.input_path}' to PDF."
            ) from e

        if not os.path.isfile(paths.output_path):
            raise DocumentConversionError(
                f"PDF output '{paths.output_filename}' was not created by LibreOffice."
            )
        return True

    def convert_docx_to_pdf(self, filename: str) -> str:
        paths = self._prepare_conversion_paths(filename, "pdf")

        if self._convert_docx_via_libreoffice(paths):
            return paths.output_filename

        try:
            docx2pdf_module = importlib.import_module("docx2pdf")
            docx2pdf_module.convert(paths.input_path, paths.output_path)
        except ImportError as e:
            raise DocumentConversionError(
                "LibreOffice or docx2pdf is required for DOCX to PDF conversion."
            ) from e
        except Exception as e:
            raise DocumentConversionError(
                f"Failed to convert '{filename}' to PDF."
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
        except Exception as e:
            raise DocumentConversionError(
                f"Failed to convert '{filename}' to DOCX."
            ) from e

        return paths.output_filename
