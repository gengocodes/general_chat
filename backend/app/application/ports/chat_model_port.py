"""Port defining the chat model interface."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import AsyncGenerator
from app.domain.entities.message import ChatMessage
from app.domain.events import AgentStreamEvent


class ChatModelPort(ABC):  # pylint: disable=too-few-public-methods
    """Port for interacting with an AI chat model."""

    @abstractmethod
    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        history: Sequence[ChatMessage] = (),
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Stream events during chat processing."""
