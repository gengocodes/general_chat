"""Presentation schemas for chat requests and responses."""

from typing import Literal
from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    """Schema representing a past message turn in the conversation"""

    role: Literal["user", "assistant"] = Field(..., description="Sender role")
    content: str = Field(
        ..., min_length=1, max_length=5000, description="Message text content"
    )


class ChatRequest(BaseModel):
    """Chat request schema with optional attached file IDs/names"""

    message: str = Field(..., min_length=1, description="User prompt or instruction")
    history: list[ChatHistoryMessage] = Field(
        default_factory=list, description="Prior conversation history"
    )
    attached_files: list[str] = Field(
        default_factory=list, description="List of attached filenames or paths in uploads/"
    )
