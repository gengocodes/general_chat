"""Unit and API integration tests for Bucket-Manager."""

import io
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import httpx
import pytest

from app.domain.entities.object_item import sanitize_filename
from app.domain.errors import (
    InvalidObjectError,
    ObjectNotFoundError,
    ObjectSizeLimitExceededError,
)
from app.application.use_cases.object_ops import (
    DeleteObjectUseCase,
    DownloadObjectBytesUseCase,
    GetPresignedUrlUseCase,
    UploadObjectUseCase,
)
from app.infrastructure.storage.r2_storage_adapter import R2StorageAdapter
from app.presentation.dependencies import get_storage_adapter
from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-Internal-API-Key": "test-internal-api-key"}


def _build_mock_r2_adapter(mock_http: MagicMock | None = None) -> R2StorageAdapter:
    if mock_http is None:
        mock_http = MagicMock(spec=httpx.Client)
        mock_http.put.return_value = MagicMock(status_code=200, is_success=True)
        mock_http.head.return_value = MagicMock(status_code=200, is_success=True)
        mock_http.get.return_value = MagicMock(
            status_code=200, is_success=True, content=b"raw-pdf-bytes"
        )
        mock_http.delete.return_value = MagicMock(status_code=204, is_success=True)

    return R2StorageAdapter(
        endpoint_url="https://dummy-account.r2.cloudflarestorage.com",
        access_key_id="dummy-access-key",
        secret_access_key="dummy-secret-key",
        bucket_name="test-bucket",
        presigned_expiry_seconds=900,
        retention_hours=24,
        http_client=mock_http,
    )


def test_health_check():
    """Verify health endpoint is accessible without internal API key."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "bucket-manager"}


def test_unauthorized_without_internal_api_key():
    """Verify object endpoints reject requests missing or having invalid X-Internal-API-Key."""
    res_missing = client.get("/api/objects/sample.pdf/presigned")
    assert res_missing.status_code == 422

    res_wrong = client.get(
        "/api/objects/sample.pdf/presigned",
        headers={"X-Internal-API-Key": "wrong-key"},
    )
    assert res_wrong.status_code == 401


def test_r2_adapter_and_use_cases():
    """Verify upload, presigned URL generation, content download, and deletion use cases."""
    mock_http = MagicMock(spec=httpx.Client)
    mock_http.put.return_value = MagicMock(status_code=200, is_success=True)
    mock_http.head.return_value = MagicMock(status_code=200, is_success=True)
    mock_http.get.return_value = MagicMock(
        status_code=200, is_success=True, content=b"raw-pdf-bytes"
    )
    mock_http.delete.return_value = MagicMock(status_code=204, is_success=True)

    adapter = _build_mock_r2_adapter(mock_http)

    upload_uc = UploadObjectUseCase(storage=adapter, max_upload_bytes=100)
    stored = upload_uc.execute(
        "report.pdf", io.BytesIO(b"hello world"), "application/pdf"
    )

    assert stored.object_key.endswith("_report.pdf")
    assert stored.original_name == "report.pdf"
    assert stored.size_bytes == 11
    assert "X-Amz-Signature=" in stored.download_url

    presign_uc = GetPresignedUrlUseCase(storage=adapter)
    presigned = presign_uc.execute(stored.object_key)
    assert presigned.object_key == stored.object_key
    assert presigned.expires_in_seconds == 900
    assert "X-Amz-Signature=" in presigned.download_url

    download_uc = DownloadObjectBytesUseCase(storage=adapter)
    obj_content = download_uc.execute(stored.object_key)
    assert obj_content.content == b"raw-pdf-bytes"

    delete_uc = DeleteObjectUseCase(storage=adapter)
    delete_uc.execute(stored.object_key)
    assert mock_http.delete.called


def test_upload_size_limit_and_invalid_filename():
    """Verify oversized uploads and empty filenames raise domain exceptions."""
    adapter = _build_mock_r2_adapter()
    upload_uc = UploadObjectUseCase(storage=adapter, max_upload_bytes=5)

    with pytest.raises(ObjectSizeLimitExceededError):
        upload_uc.execute("big.pdf", io.BytesIO(b"0123456789"))

    with pytest.raises(InvalidObjectError):
        sanitize_filename("   ")


def test_api_upload_presign_content_and_404():
    """Verify FastAPI object routes with dependency-overridden R2StorageAdapter."""
    mock_http = MagicMock(spec=httpx.Client)
    mock_http.put.return_value = MagicMock(status_code=200, is_success=True)
    mock_http.head.return_value = MagicMock(status_code=200, is_success=True)
    mock_http.get.return_value = MagicMock(
        status_code=200, is_success=True, content=b"raw-pdf-bytes"
    )
    mock_http.delete.return_value = MagicMock(status_code=204, is_success=True)

    adapter = _build_mock_r2_adapter(mock_http)
    app.dependency_overrides[get_storage_adapter] = lambda: adapter

    try:
        files = {
            "file": (
                "contract.docx",
                io.BytesIO(b"docx-bytes"),
                "application/vnd.openxmlformats",
            )
        }
        up_res = client.post("/api/objects/upload", files=files, headers=AUTH_HEADERS)
        assert up_res.status_code == 200
        payload = up_res.json()
        object_key = payload["object_key"]
        assert object_key.endswith("_contract.docx")

        pre_res = client.get(
            f"/api/objects/{object_key}/presigned", headers=AUTH_HEADERS
        )
        assert pre_res.status_code == 200
        assert "X-Amz-Signature=" in pre_res.json()["download_url"]

        content_res = client.get(
            f"/api/objects/{object_key}/content", headers=AUTH_HEADERS
        )
        assert content_res.status_code == 200
        assert content_res.content == b"raw-pdf-bytes"

        # Simulate 404 from R2
        mock_http.head.return_value = MagicMock(status_code=404, is_success=False)
        missing_res = client.get(
            "/api/objects/missing.pdf/presigned", headers=AUTH_HEADERS
        )
        assert missing_res.status_code == 404
        with pytest.raises(ObjectNotFoundError):
            adapter.create_presigned_download("missing.pdf")
    finally:
        app.dependency_overrides.pop(get_storage_adapter, None)
