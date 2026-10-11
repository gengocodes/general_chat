"""
File upload and download endpoints for GenChat
"""

import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from app.core.config import settings
from app.schemas.file import FileUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the server for processing."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    # Sanitize filename
    clean_filename = os.path.basename(file.filename)
    target_path = os.path.join(settings.UPLOAD_DIR, clean_filename)

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        size_bytes = os.path.getsize(target_path)
        logger.info("Uploaded file saved: %s (%d bytes)", target_path, size_bytes)

        return FileUploadResponse(
            filename=clean_filename,
            original_name=file.filename,
            size_bytes=size_bytes,
            file_path=target_path,
            download_url=f"/api/files/download/{clean_filename}",
        )
    except Exception as e:
        logger.exception("Failed to save uploaded file: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file: {str(e)}",
        )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a file from the uploads directory."""
    clean_filename = os.path.basename(filename)
    target_path = os.path.join(settings.UPLOAD_DIR, clean_filename)

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file not found.",
        )

    return FileResponse(
        path=target_path,
        filename=clean_filename,
        media_type="application/octet-stream",
    )
