"""Transport DTO schemas for bucket object endpoints."""

from datetime import datetime
from pydantic import BaseModel, Field


class ObjectUploadResponse(BaseModel):
    """Response returned upon uploading an object to Cloudflare R2."""

    object_key: str = Field(..., description="UUID-prefixed object key in R2")
    original_name: str = Field(..., description="Sanitized original filename")
    size_bytes: int = Field(..., description="Object size in bytes")
    download_url: str = Field(..., description="Short-lived presigned R2 download URL")
    expires_at: datetime = Field(
        ..., description="UTC timestamp when the object is scheduled for 24h auto-deletion"
    )


class PresignedUrlResponse(BaseModel):
    """Response returned when requesting a fresh presigned download URL."""

    object_key: str = Field(..., description="Object key in R2")
    download_url: str = Field(..., description="Short-lived presigned R2 download URL")
    expires_in_seconds: int = Field(..., description="Presigned URL validity in seconds")


class DeleteObjectResponse(BaseModel):
    """Response returned when deleting an object from R2."""

    object_key: str = Field(..., description="Deleted object key")
    deleted: bool = Field(..., description="Whether deletion succeeded")
