"""
LangChain document processing tools for GenChat
"""

from collections.abc import Callable
import logging
from langchain_core.tools import tool, BaseTool
from app.domain.entities.file import StoredFile
from app.domain.tools import AgentToolResult, DocumentConvertResult, ToolActivityLabels
from app.application.ports.document_processor_port import DocumentProcessorPort

logger = logging.getLogger(__name__)

DOCUMENT_TOOL_ACTIVITY_LABELS: dict[str, ToolActivityLabels] = {
    "convert_docx_to_pdf": ToolActivityLabels(
        in_progress="Converting DOCX to PDF...",
        completed="Converted DOCX to PDF",
    ),
    "convert_pdf_to_docx": ToolActivityLabels(
        in_progress="Converting PDF to DOCX...",
        completed="Converted PDF to DOCX",
    ),
}


def _execute_conversion(
    filename: str,
    output_format: str,
    converter_fn: Callable[[str], StoredFile],
) -> AgentToolResult[DocumentConvertResult]:
    """Execute a document conversion function and wrap the result in AgentToolResult."""
    format_label = output_format.upper()
    try:
        stored_output = converter_fn(filename)
        return AgentToolResult[DocumentConvertResult](
            success=True,
            message=f"Successfully converted '{filename}' to {format_label}.",
            data=DocumentConvertResult(
                original_filename=filename,
                converted_filename=stored_output.filename,
                output_format=output_format,
                download_url=stored_output.download_url,
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
) -> list[BaseTool]:
    """Factory creating LangChain tools bound to DocumentProcessorPort."""

    @tool
    def convert_docx_to_pdf(filename: str) -> AgentToolResult[DocumentConvertResult]:
        """
        Converts an uploaded DOCX Microsoft Word file to PDF format.

        Requires:
        - filename: The uploaded DOCX file key (e.g. 'a1b2c3d4e5f6_report.docx')
        """
        return _execute_conversion(
            filename=filename,
            output_format="pdf",
            converter_fn=document_processor.convert_docx_to_pdf,
        )

    @tool
    def convert_pdf_to_docx(filename: str) -> AgentToolResult[DocumentConvertResult]:
        """
        Converts an uploaded PDF document into an editable Microsoft Word DOCX file.

        Requires:
        - filename: The uploaded PDF file key (e.g. 'a1b2c3d4e5f6_contract.pdf')
        """
        return _execute_conversion(
            filename=filename,
            output_format="docx",
            converter_fn=document_processor.convert_pdf_to_docx,
        )

    return [convert_docx_to_pdf, convert_pdf_to_docx]
