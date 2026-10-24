"""API integration tests for GenChat endpoints."""

import io
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.presentation import dependencies
from app.presentation.dependencies import get_stream_chat_use_case
from app.presentation.routers.upload import upload_file
from app.application.use_cases.chat import StreamChatMessageUseCase
from app.domain.events import StreamTokenEvent, StreamCompleteEvent

client = TestClient(app)


def test_health_check():
    """Verify health endpoint returns status ok and app name."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "GenChat"}


def test_upload_and_download_flow(tmp_path, monkeypatch):
    """Verify file upload, download, and 404 behavior on missing file."""
    # Point storage to tmp_path for isolated test
    test_storage = dependencies.LocalStorageAdapter(upload_dir=str(tmp_path))
    monkeypatch.setattr(dependencies, "_storage_adapter", test_storage)

    file_content = b"Integration test file bytes"
    files = {"file": ("test_upload.txt", io.BytesIO(file_content), "text/plain")}

    # 1. Upload
    upload_res = client.post("/api/files/upload", files=files)
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["filename"] == "test_upload.txt"
    assert data["size_bytes"] == len(file_content)
    assert data["download_url"] == "/api/files/download/test_upload.txt"

    # 2. Download
    download_res = client.get("/api/files/download/test_upload.txt")
    assert download_res.status_code == 200
    assert download_res.content == file_content

    # 3. Missing file returns 404
    missing_res = client.get("/api/files/download/missing_doc.txt")
    assert missing_res.status_code == 404
    assert missing_res.json() == {"detail": "Requested file not found."}


@pytest.mark.anyio
async def test_upload_empty_filename_validation(tmp_path):
    """Verify upload endpoint rejects empty or whitespace filename with HTTP 400."""
    mock_file = MagicMock()
    mock_file.filename = "   "
    storage = dependencies.LocalStorageAdapter(upload_dir=str(tmp_path))
    use_case = dependencies.UploadFileUseCase(storage=storage)
    with pytest.raises(HTTPException) as exc_info:
        await upload_file(file=mock_file, use_case=use_case)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Filename cannot be empty or invalid."


def test_upload_oversized_file_returns_413(tmp_path, monkeypatch):
    """Verify upload endpoint rejects files exceeding max_upload_bytes with HTTP 413."""
    test_storage = dependencies.LocalStorageAdapter(
        upload_dir=str(tmp_path), max_upload_bytes=10
    )
    monkeypatch.setattr(dependencies, "_storage_adapter", test_storage)

    files = {"file": ("large.bin", io.BytesIO(b"0123456789ABCDEF"), "application/octet-stream")}
    res = client.post("/api/files/upload", files=files)
    assert res.status_code == 413



def test_upload_missing_file_payload():
    """Verify upload endpoint returns 422 if file payload is absent."""
    res = client.post("/api/files/upload")
    assert res.status_code == 422


def test_chat_stream_endpoint():
    """Verify SSE streaming chat endpoint emits correct event stream."""
    async def fake_stream(*_args, **_kwargs):
        yield StreamTokenEvent(token="tok1")
        yield StreamCompleteEvent()

    mock_use_case = MagicMock(spec=StreamChatMessageUseCase)
    mock_use_case.execute = fake_stream

    app.dependency_overrides[get_stream_chat_use_case] = lambda: mock_use_case
    try:
        res = client.post("/api/chat/stream", json={"message": "hello"})
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body_text = res.text
        assert 'data: {"type":"token","token":"tok1"}\n\n' in body_text
        assert 'data: {"type":"complete"}\n\n' in body_text
    finally:
        app.dependency_overrides.pop(get_stream_chat_use_case, None)
