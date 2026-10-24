"""Pytest configuration for Document-Processor tests."""

import os

os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")
os.environ.setdefault("BUCKET_MANAGER_URL", "http://bucket-manager.test:8001")
