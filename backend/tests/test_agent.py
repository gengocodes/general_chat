"""Unit and use case tests for GenChat agent and microservice adapters."""

from unittest.mock import MagicMock, patch
import io
import httpx
import pytest
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    ToolCall,
    ToolMessage,
)

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
from app.infrastructure.document.document_processor_adapter import (
    DocumentProcessorHttpAdapter,
)
from app.infrastructure.llm.langchain_adapter import LangChainChatAdapter
from app.infrastructure.llm.tool_executor import ToolExecutor
from app.infrastructure.storage.bucket_manager_adapter import (
    BucketManagerStorageAdapter,
)
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

    greeting = "Hello! I am Gengo, an AI assistant."
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
            attached_files=["a1b2c3d4e5f6_report.pdf"],
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
    messages: list[BaseMessage] = []
    tool_calls = [ToolCall(name="hallucinated_tool", args={"x": 1}, id="call-1")]

    results = await executor.execute(tool_calls, messages)
    assert len(results) == 1
    assert not results[0].success
    assert results[0].error_message is not None
    assert "Unknown tool 'hallucinated_tool'" in results[0].error_message
    assert len(messages) == 1
    tool_message = messages[0]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.tool_call_id == "call-1"


def test_bucket_manager_storage_adapter_and_use_cases():
    """Verify file upload, size limit enforcement, and download resolution via bucket-manager."""
    storage = BucketManagerStorageAdapter(
        base_url="http://bucket-manager.test:8001",
        internal_api_key="test-internal-api-key",
        auth=httpx.Auth(),
        max_upload_bytes=100,
    )
    upload_use_case = UploadFileUseCase(storage=storage)
    download_use_case = GetFileDownloadUseCase(storage=storage)

    file_bytes = b"Hello world text content"

    mock_upload_res = MagicMock(
        status_code=200,
        is_success=True,
    )
    mock_upload_res.json.return_value = {
        "object_key": "a1b2c3d4e5f6_test_doc.pdf",
        "original_name": "test_doc.pdf",
        "size_bytes": len(file_bytes),
        "download_url": "https://r2.example.com/a1b2c3d4e5f6_test_doc.pdf?sig=1",
    }

    with patch("httpx.post", return_value=mock_upload_res):
        stored = upload_use_case.execute(
            original_name="test_doc.pdf", file_obj=io.BytesIO(file_bytes)
        )

    assert stored.filename == "a1b2c3d4e5f6_test_doc.pdf"
    assert stored.original_name == "test_doc.pdf"
    assert stored.size_bytes == len(file_bytes)
    assert stored.download_url.startswith("https://r2.example.com/")

    mock_presign_res = MagicMock(status_code=200, is_success=True)
    mock_presign_res.json.return_value = {
        "object_key": "a1b2c3d4e5f6_test_doc.pdf",
        "download_url": "https://r2.example.com/a1b2c3d4e5f6_test_doc.pdf?sig=2",
        "expires_in_seconds": 900,
    }

    with patch("httpx.get", return_value=mock_presign_res):
        download = download_use_case.execute("a1b2c3d4e5f6_test_doc.pdf")

    assert download.filename == "a1b2c3d4e5f6_test_doc.pdf"
    assert download.download_url.endswith("sig=2")

    mock_404_res = MagicMock(status_code=404, is_success=False)
    with patch("httpx.get", return_value=mock_404_res):
        with pytest.raises(FileNotFoundDomainError):
            download_use_case.execute("non_existent_file.pdf")

    with pytest.raises(InvalidFileError):
        upload_use_case.execute("   ", io.BytesIO(b"data"))

    with pytest.raises(InvalidFileError):
        upload_use_case.execute("unsupported_notes.txt", io.BytesIO(b"data"))

    with pytest.raises(FileSizeLimitExceededError):
        upload_use_case.execute("oversized.pdf", io.BytesIO(b"x" * 101))


def test_document_processor_http_adapter():
    """Verify DocumentProcessorHttpAdapter delegates conversions over HTTP."""
    adapter = DocumentProcessorHttpAdapter(
        base_url="http://document-processor.test:8002",
        internal_api_key="test-internal-api-key",
        auth=httpx.Auth(),
    )
    mock_res = MagicMock(status_code=200, is_success=True)
    mock_res.json.return_value = {
        "original_filename": "a1b2c3d4e5f6_report.docx",
        "converted_filename": "f9e8d7c6b5a4_report.pdf",
        "original_name": "report.pdf",
        "size_bytes": 2048,
        "output_format": "pdf",
        "download_url": "https://r2.example.com/f9e8d7c6b5a4_report.pdf?sig=1",
    }

    with patch("httpx.post", return_value=mock_res):
        stored = adapter.convert_docx_to_pdf("a1b2c3d4e5f6_report.docx")

    assert stored.filename == "f9e8d7c6b5a4_report.pdf"
    assert stored.original_name == "report.pdf"
    assert stored.size_bytes == 2048
    assert stored.download_url.startswith("https://r2.example.com/")
