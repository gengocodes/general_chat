"""Pytest configuration and dummy environment variables for Bucket-Manager."""

import os

os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")
os.environ.setdefault("R2_ENDPOINT_URL", "https://dummy-account.r2.cloudflarestorage.com")
os.environ.setdefault("R2_ACCESS_KEY_ID", "dummy-access-key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "dummy-secret-key")
os.environ.setdefault("R2_BUCKET_NAME", "genchat-test-bucket")
