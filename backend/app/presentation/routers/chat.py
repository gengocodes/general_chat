"""
Chat endpoint with SSE streaming for GenChat AI Agent
"""

from collections.abc import AsyncGenerator, Sequence
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.domain.entities.message import ChatMessage
from app.domain.events import AgentStreamEvent, StreamErrorEvent
from app.application.use_cases.chat import StreamChatMessageUseCase
from app.presentation.schemas.chat import ChatHistoryMessage, ChatRequest
from app.presentation.dependencies import (
    chat_rate_limiter,
    get_stream_chat_use_case,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _to_domain_history(
    history: Sequence[ChatHistoryMessage],
) -> list[ChatMessage]:
    """Map transport ChatHistoryMessage DTOs into domain ChatMessage entities."""
    return [ChatMessage(role=msg.role, content=msg.content) for msg in history]


def _format_sse_event(event: AgentStreamEvent) -> str:
    """Serialize a domain stream event as a Server-Sent Event frame."""
    return f"data: {event.model_dump_json()}\n\n"


@router.post(
    "/stream",
    response_class=StreamingResponse,
    dependencies=[Depends(chat_rate_limiter)],
)
async def chat_stream(
    request: ChatRequest,
    use_case: StreamChatMessageUseCase = Depends(get_stream_chat_use_case),
) -> StreamingResponse:
    """Server-Sent Events (SSE) streaming chat endpoint."""
    domain_history = _to_domain_history(request.history)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in use_case.execute(
                user_message=request.message,
                history=domain_history,
                attached_files=request.attached_files,
            ):
                yield _format_sse_event(event)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Error in chat_stream endpoint: %s", str(e))
            err_event = StreamErrorEvent(
                error="Failed to generate AI response. Please try again later."
            )
            yield _format_sse_event(err_event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
