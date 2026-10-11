"""
LangChain document processing tools for GenChat
"""

import logging
from langchain_core.tools import tool, BaseTool
from app.schemas.chat import AgentToolResult, DocumentConvertResult
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


def create_document_tools(document_service: DocumentService) -> list[BaseTool]:
    """Factory creating LangChain tools bound to the DocumentService instance."""

    @tool
    def convert_docx_to_pdf(filename: str) -> AgentToolResult[DocumentConvertResult]:
        """
        Converts an uploaded DOCX Microsoft Word file to PDF format.

        Requires:
        - filename: The filename of the uploaded DOCX file in the uploads directory (e.g. 'report.docx')
        """
        try:
            pdf_filename = document_service.convert_docx_to_pdf(filename)
            download_url = f"/api/files/download/{pdf_filename}"
            return AgentToolResult[DocumentConvertResult](
                success=True,
                message=f"Successfully converted '{filename}' to PDF.",
                data=DocumentConvertResult(
                    original_filename=filename,
                    converted_filename=pdf_filename,
                    output_format="pdf",
                    download_url=download_url,
                ),
            )
        except Exception as e:
            logger.exception("Error converting %s to PDF: %s", filename, str(e))
            return AgentToolResult[DocumentConvertResult](
                success=False,
                message=f"Failed to convert '{filename}' to PDF: {str(e)}",
                data=None,
            )

    @tool
    def convert_pdf_to_docx(filename: str) -> AgentToolResult[DocumentConvertResult]:
        """
        Converts an uploaded PDF document into an editable Microsoft Word DOCX file.

        Requires:
        - filename: The filename of the uploaded PDF file in the uploads directory (e.g. 'contract.pdf')
        """
        try:
            docx_filename = document_service.convert_pdf_to_docx(filename)
            download_url = f"/api/files/download/{docx_filename}"
            return AgentToolResult[DocumentConvertResult](
                success=True,
                message=f"Successfully converted '{filename}' to DOCX.",
                data=DocumentConvertResult(
                    original_filename=filename,
                    converted_filename=docx_filename,
                    output_format="docx",
                    download_url=download_url,
                ),
            )
        except Exception as e:
            logger.exception("Error converting %s to DOCX: %s", filename, str(e))
            return AgentToolResult[DocumentConvertResult](
                success=False,
                message=f"Failed to convert '{filename}' to DOCX: {str(e)}",
                data=None,
            )

    return [convert_docx_to_pdf, convert_pdf_to_docx]
