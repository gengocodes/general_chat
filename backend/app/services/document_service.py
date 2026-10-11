import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service handling document operations."""

    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir

    def get_full_path(self, filename: str) -> str:
        # Prevent directory traversal
        clean_name = os.path.basename(filename)
        return os.path.join(self.upload_dir, clean_name)

    def convert_docx_to_pdf(self, filename: str) -> str:
        """
        Converts a DOCX file to PDF in the upload directory.
        Returns the output PDF filename.
        """
        input_path = self.get_full_path(filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File '{filename}' does not exist.")

        base_name, _ = os.path.splitext(os.path.basename(input_path))
        output_filename = f"{base_name}.pdf"
        output_path = os.path.join(self.upload_dir, output_filename)

        logger.info("Converting %s to %s", input_path, output_path)

        # NOTE: You can integrate docx2pdf, LibreOffice headless, or weasyprint here:
        # e.g.:
        # from docx2pdf import convert
        # convert(input_path, output_path)
        #
        # For boilerplate/mock fallback if libraries are not installed on host:
        try:
            from docx2pdf import convert
            convert(input_path, output_path)
        except ImportError:
            logger.warning("docx2pdf not installed. Generating dummy converted file for demonstration.")
            with open(output_path, "wb") as f:
                f.write(b"%PDF-1.4 Mock Converted Document")

        return output_filename

    def convert_pdf_to_docx(self, filename: str) -> str:
        """
        Converts a PDF file to DOCX in the upload directory.
        Returns the output DOCX filename.
        """
        input_path = self.get_full_path(filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File '{filename}' does not exist.")

        base_name, _ = os.path.splitext(os.path.basename(input_path))
        output_filename = f"{base_name}.docx"
        output_path = os.path.join(self.upload_dir, output_filename)

        logger.info("Converting %s to %s", input_path, output_path)

        # NOTE: You can integrate pdf2docx:
        # from pdf2docx import Converter
        # cv = Converter(input_path)
        # cv.convert(output_path)
        # cv.close()
        try:
            from pdf2docx import Converter
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
        except ImportError:
            logger.warning("pdf2docx not installed. Generating dummy converted file for demonstration.")
            with open(output_path, "wb") as f:
                f.write(b"Mock Converted DOCX Document")

        return output_filename
