"""Pytest test configuration and fixtures."""

import os


# Ensure required environment variables for test execution
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("GEMINI_MODEL", "gemini-test-model")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
os.environ.setdefault("BUCKET_MANAGER_URL", "http://bucket-manager.test:8001")
os.environ.setdefault("DOCUMENT_PROCESSOR_URL", "http://document-processor.test:8002")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")
