"""Application settings and environment configuration for Bucket-Manager."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings loaded from environment or .env file."""

    INTERNAL_API_KEY: str = Field(
        ...,
        min_length=1,
        description="Shared secret key for internal service-to-service authentication",
    )
    R2_ENDPOINT_URL: str = Field(
        ...,
        min_length=1,
        description="Cloudflare R2 S3-compatible endpoint URL",
    )
    R2_ACCESS_KEY_ID: str = Field(
        ...,
        min_length=1,
        description="Cloudflare R2 access key ID",
    )
    R2_SECRET_ACCESS_KEY: str = Field(
        ...,
        min_length=1,
        description="Cloudflare R2 secret access key",
    )
    R2_BUCKET_NAME: str = Field(
        ...,
        min_length=1,
        description="Cloudflare R2 bucket name",
    )
    PRESIGNED_URL_EXPIRY_SECONDS: int = Field(
        default=900,
        ge=60,
        le=86400,
        description="Presigned download URL expiration time in seconds (default 15 minutes)",
    )
    FILE_RETENTION_HOURS: int = Field(
        default=24,
        ge=1,
        description="File retention window in hours before automatic cleanup",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
