"""Presentation schemas for file operations."""

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response returned upon uploading a file"""

    filename: str = Field(..., description="Sanitized saved filename")
    original_name: str = Field(..., description="Original uploaded filename")
    size_bytes: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="Relative storage path")
    download_url: str = Field(..., description="API download URL")
