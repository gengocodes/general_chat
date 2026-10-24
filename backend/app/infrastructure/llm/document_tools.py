"""
LangChain document processing tools for GenChat
"""

from collections.abc import Callable
import logging
from langchain_core.tools import tool, BaseTool
from app.domain.tools import AgentToolResult, DocumentConvertResult
from app.application.ports.document_processor_port import DocumentProcessorPort

logger = logging.getLogger(__name__)


def _execute_conversion(
    filename: str,
    output_format: str,
    converter_fn: Callable[[str], str],
    build_download_url: Callable[[str], str],
) -> AgentToolResult[DocumentConvertResult]:
    """Execute a document conversion function and wrap the result in AgentToolResult."""
    format_label = output_format.upper()
    try:
        converted_filename = converter_fn(filename)
        return AgentToolResult[DocumentConvertResult](
            success=True,
            message=f"Successfully converted '{filename}' to {format_label}.",
            data=DocumentConvertResult(
                original_filename=filename,
                converted_filename=converted_filename,
                output_format=output_format,
                download_url=build_download_url(converted_filename),
            ),
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Error converting %s to %s: %s", filename, format_label, str(e))
        return AgentToolResult[DocumentConvertResult](
            success=False,
            message=f"Failed to convert '{filename}' to {format_label}: {str(e)}",
            data=None,
        )


def create_document_tools(
    document_processor: DocumentProcessorPort,
    build_download_url: Callable[[str], str],
) -> list[BaseTool]:
    """Factory creating LangChain tools bound to DocumentProcessorPort."""

    @tool
    def convert_docx_to_pdf(filename: str) -> AgentToolResult[DocumentConvertResult]:
        """
        Converts an uploaded DOCX Microsoft Word file to PDF format.

        Requires:
        - filename: The filename of the uploaded DOCX file in the uploads
          directory (e.g. 'report.docx')
        """
        return _execute_conversion(
            filename=filename,
            output_format="pdf",
            converter_fn=document_processor.convert_docx_to_pdf,
            build_download_url=build_download_url,
        )

    @tool
    def convert_pdf_to_docx(filename: str) -> AgentToolResult[DocumentConvertResult]:
        """
        Converts an uploaded PDF document into an editable Microsoft Word DOCX file.

        Requires:
        - filename: The filename of the uploaded PDF file in the uploads
          directory (e.g. 'contract.pdf')
        """
        return _execute_conversion(
            filename=filename,
            output_format="docx",
            converter_fn=document_processor.convert_pdf_to_docx,
            build_download_url=build_download_url,
        )

    return [convert_docx_to_pdf, convert_pdf_to_docx]
