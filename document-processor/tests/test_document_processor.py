"""Unit and API integration tests for the Document-Processor microservice."""

from unittest.mock import MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.domain.entities.conversion import (
    ConvertedDocument,
    extract_original_base_name,
    sanitize_filename,
)
from app.domain.errors import (
    DocumentConversionError,
    InvalidDocumentError,
    SourceDocumentNotFoundError,
)
from app.application.use_cases.convert_document import ConvertDocumentUseCase
from app.infrastructure.converter.document_converter_adapter import (
    DocumentConverterAdapter,
)
from app.main import app
from app.presentation.dependencies import get_converter_adapter

client = TestClient(app)
AUTH_HEADERS = {"X-Internal-API-Key": "test-internal-api-key"}


def test_health_check():
    """Verify /health returns 200 OK without requiring internal auth."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy", "service": "genchat-document-processor"}


def test_unauthorized_without_internal_api_key():
    """Verify /api/documents/convert rejects missing or invalid X-Internal-API-Key."""
    res_missing = client.post(
        "/api/documents/convert",
        json={"filename": "a1b2c3d4e5f6_report.docx", "target_format": "pdf"},
    )
    assert res_missing.status_code == 422

    res_wrong = client.post(
        "/api/documents/convert",
        json={"filename": "a1b2c3d4e5f6_report.docx", "target_format": "pdf"},
        headers={"X-Internal-API-Key": "wrong-key"},
    )
    assert res_wrong.status_code == 401


def test_domain_filename_helpers():
    """Verify filename sanitization and UUID prefix extraction."""
    assert sanitize_filename("  ../folder/report.docx  ") == "report.docx"
    assert extract_original_base_name("a1b2c3d4e5f6_report.docx") == "report"
    assert extract_original_base_name("report.docx") == "report"

    with pytest.raises(InvalidDocumentError):
        sanitize_filename("   ")


def test_document_converter_adapter_and_use_case():
    """Verify DocumentConverterAdapter stages bytes, converts, and uploads output."""
    mock_http = MagicMock(spec=httpx.Client)
    mock_http.get.return_value = MagicMock(
        status_code=200, is_success=True, content=b"fake-docx-bytes"
    )
    upload_response = MagicMock(status_code=200, is_success=True)
    upload_response.json.return_value = {
        "object_key": "f9e8d7c6b5a4_report.pdf",
        "original_name": "report.pdf",
        "size_bytes": 512,
        "download_url": "https://r2.example.com/f9e8d7c6b5a4_report.pdf?sig=1",
    }
    mock_http.post.return_value = upload_response

    adapter = DocumentConverterAdapter(
        bucket_manager_url="http://bucket-manager.test:8001",
        internal_api_key="test-internal-api-key",
        auth=httpx.Auth(),
        http_client=mock_http,
    )
    use_case = ConvertDocumentUseCase(converter=adapter)

    def _fake_libreoffice(paths):
        with open(paths.output_path, "wb") as out_f:
            out_f.write(b"%PDF-1.4 converted")
        return True

    with patch.object(
        DocumentConverterAdapter,
        "_convert_docx_via_libreoffice",
        side_effect=_fake_libreoffice,
    ):
        result = use_case.execute("a1b2c3d4e5f6_report.docx", "pdf")

    assert result.original_filename == "a1b2c3d4e5f6_report.docx"
    assert result.converted_filename == "f9e8d7c6b5a4_report.pdf"
    assert result.original_name == "report.pdf"
    assert result.output_format == "pdf"
    assert result.size_bytes == 512
    assert result.download_url.startswith("https://r2.example.com/")

    # Verify 404 from bucket-manager raises SourceDocumentNotFoundError
    mock_http.get.return_value = MagicMock(status_code=404, is_success=False)
    with pytest.raises(SourceDocumentNotFoundError):
        use_case.execute("missing.docx", "pdf")


def test_api_convert_endpoint_and_error_mappings():
    """Verify FastAPI /api/documents/convert success and error status mappings."""
    mock_converter = MagicMock()
    mock_converter.convert_docx_to_pdf.return_value = ConvertedDocument(
        original_filename="a1b2c3d4e5f6_report.docx",
        converted_filename="f9e8d7c6b5a4_report.pdf",
        original_name="report.pdf",
        size_bytes=1024,
        output_format="pdf",
        download_url="https://r2.example.com/f9e8d7c6b5a4_report.pdf?sig=abc",
    )
    app.dependency_overrides[get_converter_adapter] = lambda: mock_converter

    try:
        res = client.post(
            "/api/documents/convert",
            json={"filename": "a1b2c3d4e5f6_report.docx", "target_format": "pdf"},
            headers=AUTH_HEADERS,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["converted_filename"] == "f9e8d7c6b5a4_report.pdf"
        assert body["output_format"] == "pdf"

        mock_converter.convert_docx_to_pdf.side_effect = SourceDocumentNotFoundError(
            "Not found"
        )
        res_404 = client.post(
            "/api/documents/convert",
            json={"filename": "missing.docx", "target_format": "pdf"},
            headers=AUTH_HEADERS,
        )
        assert res_404.status_code == 404

        mock_converter.convert_docx_to_pdf.side_effect = DocumentConversionError(
            "Conversion failed"
        )
        res_422 = client.post(
            "/api/documents/convert",
            json={"filename": "corrupt.docx", "target_format": "pdf"},
            headers=AUTH_HEADERS,
        )
        assert res_422.status_code == 422
    finally:
        app.dependency_overrides.clear()
