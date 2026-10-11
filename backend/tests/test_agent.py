from unittest.mock import MagicMock, AsyncMock
import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

from app.services.agent_service import AgentService
from app.schemas.chat import (
    StreamStatusEvent,
    StreamActivityEvent,
    StreamTokenEvent,
    StreamCompleteEvent,
)


async def _async_gen(items):
    for item in items:
        yield item


@pytest.mark.anyio
async def test_agent_stream_chat_basic_flow():
    mock_model = MagicMock()
    bound_model = MagicMock()

    greeting = "Hello! I am GenChat, Paul Corsino's AI assistant."
    chunk1 = AIMessageChunk(content=greeting)
    final_output = AIMessage(content=greeting, tool_calls=[])

    events = [
        {"event": "on_chat_model_stream", "data": {"chunk": chunk1}},
        {"event": "on_chat_model_end", "data": {"output": final_output}},
    ]

    bound_model.astream_events = MagicMock(return_value=_async_gen(events))
    mock_model.bind_tools = MagicMock(return_value=bound_model)

    service = AgentService(model=mock_model)

    emitted_events = [
        event async for event in service.stream_chat("Hi, what can you do?")
    ]

    event_types = [type(e) for e in emitted_events]
    assert StreamStatusEvent in event_types
    assert StreamActivityEvent in event_types
    assert StreamTokenEvent in event_types
    assert StreamCompleteEvent in event_types

    tokens = [e.token for e in emitted_events if isinstance(e, StreamTokenEvent)]
    assert "".join(tokens) == greeting
