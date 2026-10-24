"""Document processing implementation using ephemeral scratch directories and FileStoragePort."""

from dataclasses import dataclass
import importlib
import io
import logging
import os
import shutil
import subprocess
import tempfile
from app.domain.entities.file import (
    StoredFile,
    extract_original_base_name,
    sanitize_filename,
)
from app.domain.errors import DocumentConversionError
from app.application.ports.document_processor_port import DocumentProcessorPort
from app.application.ports.file_storage_port import FileStoragePort

logger = logging.getLogger(__name__)


# TODO: Extract DocumentService into a dedicated background worker / standalone microservice. # pylint: disable=fixme
@dataclass(frozen=True)
class ConversionPaths:
    """Resolved input and output filesystem paths inside an ephemeral temp directory."""

    temp_dir: str
    input_path: str
    output_path: str
    output_filename: str


class EphemeralDocumentService(DocumentProcessorPort):
    """DocumentProcessorPort implementation converting files in ephemeral temp dirs."""

    def __init__(self, storage: FileStoragePort):
        self._storage = storage

    def _stage_input_file(
        self, filename: str, temp_dir: str, target_ext: str
    ) -> ConversionPaths:
        """Fetch source bytes from FileStoragePort into temp_dir and return ConversionPaths."""
        clean_name = sanitize_filename(filename)
        raw_bytes = self._storage.fetch_file_bytes(clean_name)

        input_path = os.path.join(temp_dir, clean_name)
        with open(input_path, "wb") as f:
            f.write(raw_bytes)

        base_name = extract_original_base_name(clean_name)
        output_filename = f"{base_name}.{target_ext}"
        output_path = os.path.join(temp_dir, output_filename)
        logger.info("Converting staged file %s to %s", input_path, output_path)
        return ConversionPaths(
            temp_dir=temp_dir,
            input_path=input_path,
            output_path=output_path,
            output_filename=output_filename,
        )

    def _upload_converted_output(self, paths: ConversionPaths) -> StoredFile:
        """Read converted output file from disk and persist it via FileStoragePort."""
        if not os.path.isfile(paths.output_path):
            raise DocumentConversionError(
                f"Converted output '{paths.output_filename}' was not created."
            )
        with open(paths.output_path, "rb") as out_file:
            content = out_file.read()
        return self._storage.save_file(paths.output_filename, io.BytesIO(content))

    @staticmethod
    def _convert_docx_via_libreoffice(paths: ConversionPaths) -> bool:
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
                    paths.temp_dir,
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

        raw_lo_base, _ = os.path.splitext(os.path.basename(paths.input_path))
        lo_output = os.path.join(paths.temp_dir, f"{raw_lo_base}.pdf")
        if os.path.isfile(lo_output) and lo_output != paths.output_path:
            os.replace(lo_output, paths.output_path)

        return os.path.isfile(paths.output_path)

    def convert_docx_to_pdf(self, filename: str) -> StoredFile:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._stage_input_file(filename, temp_dir, "pdf")

            if not self._convert_docx_via_libreoffice(paths):
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

            return self._upload_converted_output(paths)

    def convert_pdf_to_docx(self, filename: str) -> StoredFile:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._stage_input_file(filename, temp_dir, "docx")

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

            return self._upload_converted_output(paths)
