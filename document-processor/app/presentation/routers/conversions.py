"""Internal REST endpoints for document format conversions."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.errors import (
    DocumentConversionError,
    InvalidDocumentError,
    SourceDocumentNotFoundError,
    StorageServiceError,
)
from app.application.use_cases.convert_document import ConvertDocumentUseCase
from app.presentation.dependencies import (
    get_convert_document_use_case,
    verify_internal_api_key,
)
from app.presentation.schemas.conversion_schema import (
    DocumentConvertRequest,
    DocumentConvertResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
    dependencies=[Depends(verify_internal_api_key)],
)


@router.post("/convert", response_model=DocumentConvertResponse)
async def convert_document(
    payload: DocumentConvertRequest,
    use_case: ConvertDocumentUseCase = Depends(get_convert_document_use_case),
) -> DocumentConvertResponse:
    """Convert a stored document between DOCX and PDF and store the output in bucket-manager."""
    try:
        result = use_case.execute(
            filename=payload.filename,
            target_format=payload.target_format,
        )
        return DocumentConvertResponse(
            original_filename=result.original_filename,
            converted_filename=result.converted_filename,
            original_name=result.original_name,
            size_bytes=result.size_bytes,
            output_format=result.output_format,
            download_url=result.download_url,
        )
    except InvalidDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SourceDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source document not found.",
        ) from exc
    except DocumentConversionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except StorageServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service communication error.",
        ) from exc
