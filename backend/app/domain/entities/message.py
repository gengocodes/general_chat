"""
Domain entities for chat messages.
"""

from dataclasses import dataclass
from typing import Literal

MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    """Domain representation of a chat message."""

    role: MessageRole
    content: str
