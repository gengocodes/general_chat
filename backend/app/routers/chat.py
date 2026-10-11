"""
Chat endpoints with SSE streaming for GenChat AI Agent
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, StreamErrorEvent
from app.services.agent_service import AgentService, AgentServiceError
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def get_agent_service() -> AgentService:
    """Dependency provider creating AgentService."""
    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )
    document_service = DocumentService(settings.UPLOAD_DIR)
    return AgentService(model=model, document_service=document_service)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    """Non-streaming chat endpoint."""
    try:
        return await agent_service.chat(
            user_message=request.message,
            history=request.history,
            attached_files=request.attached_files,
        )
    except AgentServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI response.",
        ) from e


@router.post("/stream", response_class=StreamingResponse)
async def chat_stream(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """Server-Sent Events (SSE) streaming chat endpoint."""

    async def event_generator():
        try:
            async for event in agent_service.stream_chat(
                user_message=request.message,
                history=request.history,
                attached_files=request.attached_files,
            ):
                yield f"data: {event.model_dump_json()}\n\n"
        except Exception as e:
            logger.exception("Error in chat_stream endpoint: %s", str(e))
            err_event = StreamErrorEvent(
                error="Failed to generate AI response. Please try again later."
            )
            yield f"data: {err_event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
