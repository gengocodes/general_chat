"""Unit and use case tests for GenChat agent and storage operations."""

from unittest.mock import MagicMock
import io
import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

from app.domain.entities.message import ChatMessage
from app.domain.errors import (
    FileNotFoundDomainError,
    FileSizeLimitExceededError,
    InvalidFileError,
)
from app.domain.events import (
    StreamActivityEvent,
    StreamTokenEvent,
    StreamCompleteEvent,
)
from app.infrastructure.llm.langchain_adapter import LangChainChatAdapter
from app.infrastructure.llm.tool_executor import ToolExecutor
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from app.application.use_cases.chat import (
    StreamChatMessageUseCase,
    prepare_conversation_history,
    format_user_prompt,
)
from app.application.use_cases.file import (
    UploadFileUseCase,
    GetFileDownloadUseCase,
)


async def _async_gen(items):
    """Helper async generator to yield items."""
    for item in items:
        yield item


@pytest.mark.anyio
async def test_agent_stream_chat_basic_flow():
    """Verify stream chat use case yields expected stream events."""
    mock_model = MagicMock()
    bound_model = MagicMock()

    greeting = "Hello! I am GenChat, Paul Corsino's AI assistant."
    chunk1 = AIMessageChunk(content=greeting)
    final_output = AIMessage(content=greeting, tool_calls=[])

    events = [
        {"event": "on_chat_model_stream", "data": {"chunk": chunk1}},
        {"event": "on_chat_model_end", "data": {"output": final_output}},
    ]

    mock_stream = MagicMock(return_value=_async_gen(events))
    bound_model.astream_events = mock_stream
    mock_model.astream_events = mock_stream
    mock_model.bind_tools = MagicMock(return_value=bound_model)

    adapter = LangChainChatAdapter(model=mock_model)
    use_case = StreamChatMessageUseCase(chat_model=adapter)

    emitted_events = [
        event async for event in use_case.execute(
            user_message="Hi, what can you do?",
            history=[ChatMessage(role="user", content="prior context")],
            attached_files=["report.pdf"],
        )
    ]

    event_types = [type(e) for e in emitted_events]
    assert StreamActivityEvent in event_types
    assert StreamTokenEvent in event_types
    assert StreamCompleteEvent in event_types

    tokens = [e.token for e in emitted_events if isinstance(e, StreamTokenEvent)]
    assert "".join(tokens) == greeting


def test_history_and_prompt_formatting_helpers():
    """Verify conversation history sanitization, truncation, and prompt formatting."""
    raw_history = [
        ChatMessage(role="user", content="   "),
        *[ChatMessage(role="user", content=f"  msg-{i}  ") for i in range(12)],
    ]
    cleaned = prepare_conversation_history(raw_history)
    assert len(cleaned) == 10
    assert cleaned[0].content == "msg-2"
    assert cleaned[-1].content == "msg-11"

    prompt_no_files = format_user_prompt("Summarize", [])
    assert prompt_no_files == "Summarize"

    prompt_with_files = format_user_prompt("Summarize", ["doc1.pdf", "  ", "doc2.docx"])
    assert prompt_with_files == "Summarize\n[Attached Files: doc1.pdf, doc2.docx]"


@pytest.mark.anyio
async def test_tool_executor_handles_unknown_tool():
    """Verify ToolExecutor appends an error ToolMessage when an unknown tool is requested."""
    executor = ToolExecutor(tools=[])
    messages = []
    tool_calls = [{"name": "hallucinated_tool", "args": {"x": 1}, "id": "call-1"}]

    results = await executor.execute(tool_calls, messages)
    assert len(results) == 1
    assert not results[0].success
    assert "Unknown tool 'hallucinated_tool'" in results[0].error_message
    assert len(messages) == 1
    assert messages[0].tool_call_id == "call-1"


def test_file_storage_and_use_cases(tmp_path):
    """Verify file upload, size limit enforcement, and download use cases with local storage."""
    storage = LocalStorageAdapter(upload_dir=str(tmp_path), max_upload_bytes=100)
    upload_use_case = UploadFileUseCase(storage=storage)
    download_use_case = GetFileDownloadUseCase(storage=storage)

    file_bytes = b"Hello world text content"
    file_obj = io.BytesIO(file_bytes)

    stored = upload_use_case.execute(
        original_name="test_doc.txt", file_obj=file_obj
    )

    assert stored.filename == "test_doc.txt"
    assert stored.original_name == "test_doc.txt"
    assert stored.size_bytes == len(file_bytes)

    download = download_use_case.execute("test_doc.txt")
    assert download.filename == "test_doc.txt"
    assert download.file_path == stored.file_path

    with pytest.raises(FileNotFoundDomainError):
        download_use_case.execute("non_existent_file.pdf")

    with pytest.raises(InvalidFileError):
        upload_use_case.execute("   ", io.BytesIO(b"data"))

    with pytest.raises(FileSizeLimitExceededError):
        upload_use_case.execute("oversized.bin", io.BytesIO(b"x" * 101))
