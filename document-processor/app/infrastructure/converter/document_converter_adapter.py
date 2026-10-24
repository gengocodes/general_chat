"""Document conversion adapter backed by LibreOffice / pdf2docx and bucket-manager over HTTP."""

from dataclasses import dataclass
import importlib
import io
import logging
import os
import shutil
import subprocess
import tempfile
import httpx

from app.domain.entities.conversion import (
    ConvertedDocument,
    TargetFormat,
    extract_original_base_name,
    sanitize_filename,
)
from app.domain.errors import (
    DocumentConversionError,
    SourceDocumentNotFoundError,
    StorageServiceError,
)
from app.application.ports.document_converter_port import DocumentConverterPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversionPaths:
    """Resolved input and output filesystem paths inside a temporary working directory."""

    temp_dir: str
    input_path: str
    output_path: str
    output_filename: str


class DocumentConverterAdapter(DocumentConverterPort):
    """DocumentConverterPort implementation converting files between DOCX and PDF."""

    def __init__(
        self,
        bucket_manager_url: str,
        internal_api_key: str,
        auth: httpx.Auth,
        http_client: httpx.Client | None = None,
    ):
        self._base_url = bucket_manager_url.rstrip("/")
        self._headers = {"X-Internal-API-Key": internal_api_key}
        self._auth = auth
        self._client = http_client or httpx.Client(timeout=60.0)

    def _fetch_source_bytes(self, object_key: str) -> bytes:
        """Fetch raw source file bytes from bucket-manager."""
        try:
            response = self._client.get(
                f"{self._base_url}/api/objects/{object_key}/content",
                headers=self._headers,
                auth=self._auth,
            )
        except httpx.HTTPError as exc:
            logger.exception("Bucket-manager content fetch failed: %s", str(exc))
            raise StorageServiceError("Could not communicate with storage service.") from exc

        if response.status_code == 404:
            raise SourceDocumentNotFoundError(f"Source file '{object_key}' was not found.")
        if not response.is_success:
            raise StorageServiceError("Storage service failed to fetch source file.")
        return response.content

    def _upload_converted_bytes(
        self,
        original_filename: str,
        output_filename: str,
        content: bytes,
        output_format: TargetFormat,
    ) -> ConvertedDocument:
        """Upload converted output bytes to bucket-manager and return ConvertedDocument."""
        try:
            response = self._client.post(
                f"{self._base_url}/api/objects/upload",
                headers=self._headers,
                auth=self._auth,
                files={
                    "file": (
                        output_filename,
                        io.BytesIO(content),
                        "application/octet-stream",
                    )
                },
            )
        except httpx.HTTPError as exc:
            logger.exception("Bucket-manager upload request failed: %s", str(exc))
            raise StorageServiceError("Could not communicate with storage service.") from exc

        if not response.is_success:
            logger.error(
                "Bucket-manager returned %d on upload: %s",
                response.status_code,
                response.text,
            )
            raise StorageServiceError("Storage service failed to store converted file.")

        data = response.json()
        return ConvertedDocument(
            original_filename=original_filename,
            converted_filename=data["object_key"],
            original_name=data["original_name"],
            size_bytes=data["size_bytes"],
            output_format=output_format,
            download_url=data["download_url"],
        )

    def _stage_input_file(
        self, filename: str, temp_dir: str, target_ext: TargetFormat
    ) -> ConversionPaths:
        """Fetch source bytes from bucket-manager into temp_dir and return ConversionPaths."""
        clean_name = sanitize_filename(filename)
        raw_bytes = self._fetch_source_bytes(clean_name)

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

    def _persist_converted_output(
        self,
        original_filename: str,
        paths: ConversionPaths,
        output_format: TargetFormat,
    ) -> ConvertedDocument:
        """Read converted output file from disk and persist it to bucket-manager."""
        if not os.path.isfile(paths.output_path):
            raise DocumentConversionError(
                f"Converted output '{paths.output_filename}' was not created."
            )
        with open(paths.output_path, "rb") as out_file:
            content = out_file.read()
        return self._upload_converted_bytes(
            original_filename=original_filename,
            output_filename=paths.output_filename,
            content=content,
            output_format=output_format,
        )

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
        except (subprocess.SubprocessError, OSError) as exc:
            raise DocumentConversionError(
                f"LibreOffice failed to convert '{paths.input_path}' to PDF."
            ) from exc

        raw_lo_base, _ = os.path.splitext(os.path.basename(paths.input_path))
        lo_output = os.path.join(paths.temp_dir, f"{raw_lo_base}.pdf")
        if os.path.isfile(lo_output) and lo_output != paths.output_path:
            os.replace(lo_output, paths.output_path)

        return os.path.isfile(paths.output_path)

    def convert_docx_to_pdf(self, filename: str) -> ConvertedDocument:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._stage_input_file(filename, temp_dir, "pdf")

            if not self._convert_docx_via_libreoffice(paths):
                try:
                    docx2pdf_module = importlib.import_module("docx2pdf")
                    docx2pdf_module.convert(paths.input_path, paths.output_path)
                except ImportError as exc:
                    raise DocumentConversionError(
                        "LibreOffice or docx2pdf is required for DOCX to PDF conversion."
                    ) from exc
                except Exception as exc:
                    raise DocumentConversionError(
                        f"Failed to convert '{filename}' to PDF."
                    ) from exc

            return self._persist_converted_output(filename, paths, "pdf")

    def convert_pdf_to_docx(self, filename: str) -> ConvertedDocument:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._stage_input_file(filename, temp_dir, "docx")

            try:
                pdf2docx_module = importlib.import_module("pdf2docx")
                cv = pdf2docx_module.Converter(paths.input_path)
                cv.convert(paths.output_path)
                cv.close()
            except ImportError as exc:
                raise DocumentConversionError(
                    "pdf2docx is required for PDF to DOCX conversion but is not installed."
                ) from exc
            except Exception as exc:
                raise DocumentConversionError(
                    f"Failed to convert '{filename}' to DOCX."
                ) from exc

            return self._persist_converted_output(filename, paths, "docx")
