"""Pydantic request and response DTOs for Document-Processor endpoints."""

from pydantic import BaseModel, Field
from app.domain.entities.conversion import TargetFormat


class DocumentConvertRequest(BaseModel):
    """Transport payload requesting conversion of a stored file."""

    filename: str = Field(..., min_length=1, description="Stored object key in bucket-manager")
    target_format: TargetFormat = Field(..., description="Target format ('pdf' or 'docx')")


class DocumentConvertResponse(BaseModel):
    """Transport response returned after converting and uploading a document."""

    original_filename: str = Field(..., description="Source object key in bucket-manager")
    converted_filename: str = Field(..., description="Converted object key in bucket-manager")
    original_name: str = Field(..., description="Clean base filename with new extension")
    size_bytes: int = Field(..., ge=0, description="Converted file size in bytes")
    output_format: TargetFormat = Field(..., description="Output format ('pdf' or 'docx')")
    download_url: str = Field(..., description="Presigned R2 download URL")
