"""Composition Root and internal API key authentication for Bucket-Manager."""

from functools import lru_cache
import secrets
from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.application.ports.object_storage_port import ObjectStoragePort
from app.application.use_cases.object_ops import (
    DeleteObjectUseCase,
    DownloadObjectBytesUseCase,
    GetPresignedUrlUseCase,
    UploadObjectUseCase,
)
from app.infrastructure.storage.r2_storage_adapter import R2StorageAdapter


def verify_internal_api_key(
    x_internal_api_key: str = Header(..., alias="X-Internal-API-Key"),
) -> None:
    """Verify the shared internal API key header using constant-time comparison."""
    if not secrets.compare_digest(x_internal_api_key, settings.INTERNAL_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key.",
        )


@lru_cache(maxsize=1)
def get_storage_adapter() -> ObjectStoragePort:
    """Provide singleton R2StorageAdapter configured with Cloudflare R2 credentials."""
    return R2StorageAdapter(
        endpoint_url=settings.R2_ENDPOINT_URL,
        access_key_id=settings.R2_ACCESS_KEY_ID,
        secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        bucket_name=settings.R2_BUCKET_NAME,
        presigned_expiry_seconds=settings.PRESIGNED_URL_EXPIRY_SECONDS,
        retention_hours=settings.FILE_RETENTION_HOURS,
    )


def get_upload_object_use_case(
    storage: ObjectStoragePort = Depends(get_storage_adapter),
) -> UploadObjectUseCase:
    """Provide UploadObjectUseCase wired with ObjectStoragePort."""
    return UploadObjectUseCase(storage=storage)


def get_presigned_url_use_case(
    storage: ObjectStoragePort = Depends(get_storage_adapter),
) -> GetPresignedUrlUseCase:
    """Provide GetPresignedUrlUseCase wired with ObjectStoragePort."""
    return GetPresignedUrlUseCase(storage=storage)


def get_download_bytes_use_case(
    storage: ObjectStoragePort = Depends(get_storage_adapter),
) -> DownloadObjectBytesUseCase:
    """Provide DownloadObjectBytesUseCase wired with ObjectStoragePort."""
    return DownloadObjectBytesUseCase(storage=storage)


def get_delete_object_use_case(
    storage: ObjectStoragePort = Depends(get_storage_adapter),
) -> DeleteObjectUseCase:
    """Provide DeleteObjectUseCase wired with ObjectStoragePort."""
    return DeleteObjectUseCase(storage=storage)
