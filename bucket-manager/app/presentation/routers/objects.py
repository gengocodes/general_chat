"""Internal REST endpoints for managing Cloudflare R2 bucket objects."""

import logging
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.domain.errors import (
    InvalidObjectError,
    ObjectNotFoundError,
    ObjectSizeLimitExceededError,
    StorageProviderError,
)
from app.application.use_cases.object_ops import (
    DeleteObjectUseCase,
    DownloadObjectBytesUseCase,
    GetPresignedUrlUseCase,
    UploadObjectUseCase,
)
from app.presentation.dependencies import (
    get_delete_object_use_case,
    get_download_bytes_use_case,
    get_presigned_url_use_case,
    get_upload_object_use_case,
    verify_internal_api_key,
)
from app.presentation.schemas.object_schema import (
    DeleteObjectResponse,
    ObjectUploadResponse,
    PresignedUrlResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/objects",
    tags=["Objects"],
    dependencies=[Depends(verify_internal_api_key)],
)


@router.post("/upload", response_model=ObjectUploadResponse)
async def upload_object(
    file: UploadFile = File(...),
    use_case: UploadObjectUseCase = Depends(get_upload_object_use_case),
) -> ObjectUploadResponse:
    """Upload a file stream to Cloudflare R2 and return its object key and presigned URL."""
    try:
        stored = use_case.execute(
            original_name=file.filename or "",
            file_obj=file.file,
            content_type=file.content_type or "application/octet-stream",
        )
        return ObjectUploadResponse(
            object_key=stored.object_key,
            original_name=stored.original_name,
            size_bytes=stored.size_bytes,
            download_url=stored.download_url,
            expires_at=stored.expires_at,
        )
    except InvalidObjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ObjectSizeLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Uploaded file exceeds the 10 MB maximum size limit.",
        ) from exc
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud storage provider error.",
        ) from exc


@router.get("/{object_key}/presigned", response_model=PresignedUrlResponse)
async def get_presigned_url(
    object_key: str,
    use_case: GetPresignedUrlUseCase = Depends(get_presigned_url_use_case),
) -> PresignedUrlResponse:
    """Generate a short-lived presigned download URL for a stored object key."""
    try:
        presigned = use_case.execute(object_key)
        return PresignedUrlResponse(
            object_key=presigned.object_key,
            download_url=presigned.download_url,
            expires_in_seconds=presigned.expires_in_seconds,
        )
    except (ObjectNotFoundError, InvalidObjectError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file not found.",
        ) from exc
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud storage provider error.",
        ) from exc


@router.get("/{object_key}/content")
async def get_object_content(
    object_key: str,
    use_case: DownloadObjectBytesUseCase = Depends(get_download_bytes_use_case),
) -> Response:
    """Stream raw object bytes back to internal backend callers for document processing."""
    try:
        obj = use_case.execute(object_key)
        return Response(
            content=obj.content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{obj.object_key}"'
            },
        )
    except (ObjectNotFoundError, InvalidObjectError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file not found.",
        ) from exc
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud storage provider error.",
        ) from exc


@router.delete("/{object_key}", response_model=DeleteObjectResponse)
async def delete_object(
    object_key: str,
    use_case: DeleteObjectUseCase = Depends(get_delete_object_use_case),
) -> DeleteObjectResponse:
    """Delete an object from Cloudflare R2."""
    try:
        use_case.execute(object_key)
        return DeleteObjectResponse(object_key=object_key, deleted=True)
    except (ObjectNotFoundError, InvalidObjectError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file not found.",
        ) from exc
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud storage provider error.",
        ) from exc
