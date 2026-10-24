"""Domain models for agent tool execution results."""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class AgentToolResult(BaseModel, Generic[T]):
    """Generic strongly-typed response model for agent tools."""

    success: bool = Field(..., description="Whether the tool operation succeeded")
    message: str = Field(..., description="Human-readable result or error message")
    data: T | None = Field(default=None, description="Typed result payload")


class DocumentConvertResult(BaseModel):
    """Result payload for document tools."""

    original_filename: str = Field(..., description="Name of original file")
    converted_filename: str = Field(..., description="Name of converted file")
    output_format: str = Field(..., description="Output file extension e.g. pdf, docx")
    download_url: str = Field(..., description="Local or served URL to download the file")
