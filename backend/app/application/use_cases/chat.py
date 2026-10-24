"""Use cases for streaming chat messages and preparing conversation context."""

from collections.abc import Sequence
from typing import AsyncGenerator
from app.domain.entities.message import ChatMessage
from app.domain.events import AgentStreamEvent
from app.application.ports.chat_model_port import ChatModelPort
from app.application.prompts.agent import get_system_prompt

MAX_HISTORY_MESSAGES: int = 10


def prepare_conversation_history(
    history: Sequence[ChatMessage],
) -> list[ChatMessage]:
    """Filter out blank messages, strip whitespace, and cap history to recent turns."""
    sanitized = [
        ChatMessage(role=msg.role, content=msg.content.strip())
        for msg in history
        if msg.content and msg.content.strip()
    ]
    return sanitized[-MAX_HISTORY_MESSAGES:]


def format_user_prompt(
    user_message: str,
    attached_files: Sequence[str] = (),
) -> str:
    """Format user message and append attached file context when present."""
    clean_files = [f.strip() for f in attached_files if f and f.strip()]
    if not clean_files:
        return user_message
    files_note = f"\n[Attached Files: {', '.join(clean_files)}]"
    return f"{user_message}{files_note}"


class StreamChatMessageUseCase:  # pylint: disable=too-few-public-methods
    """Use case for executing streaming chat requests."""

    def __init__(self, chat_model: ChatModelPort):
        self._chat_model = chat_model

    async def execute(
        self,
        user_message: str,
        history: Sequence[ChatMessage] = (),
        attached_files: Sequence[str] = (),
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Execute streaming chat request and yield domain stream events."""
        prepared_history = prepare_conversation_history(history)
        formatted_prompt = format_user_prompt(user_message, attached_files)
        async for event in self._chat_model.stream_chat(
            system_prompt=get_system_prompt(),
            user_message=formatted_prompt,
            history=prepared_history,
        ):
            yield event
