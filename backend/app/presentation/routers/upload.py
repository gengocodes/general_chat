"""
File upload and download endpoints for GenChat
"""

import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.domain.errors import (
    FileNotFoundDomainError,
    FileSizeLimitExceededError,
    InvalidFileError,
)
from app.application.use_cases.file import (
    UploadFileUseCase,
    GetFileDownloadUseCase,
)
from app.presentation.schemas.file import FileUploadResponse
from app.presentation.dependencies import (
    build_file_download_url,
    get_upload_file_use_case,
    get_file_download_use_case,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    use_case: UploadFileUseCase = Depends(get_upload_file_use_case),
) -> FileUploadResponse:
    """Upload a file to the server for processing."""
    try:
        stored = use_case.execute(file.filename or "", file.file)
        return FileUploadResponse(
            filename=stored.filename,
            original_name=stored.original_name,
            size_bytes=stored.size_bytes,
            download_url=build_file_download_url(stored.filename),
        )
    except InvalidFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except FileSizeLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Uploaded file exceeds the 10 MB maximum size limit.",
        ) from exc
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to save uploaded file: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded file.",
        ) from exc


@router.get("/download/{filename}")
async def download_file(
    filename: str,
    use_case: GetFileDownloadUseCase = Depends(get_file_download_use_case),
) -> FileResponse:
    """Download a file from the uploads directory."""
    try:
        download = use_case.execute(filename)
    except (FileNotFoundDomainError, InvalidFileError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file not found.",
        ) from exc

    return FileResponse(
        path=download.file_path,
        filename=download.filename,
        media_type="application/octet-stream",
    )
