"""Application settings and environment configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings loaded from environment or .env file."""

    GEMINI_API_KEY: str = Field(
        ..., min_length=1, description="Google Gemini API key"
    )
    GEMINI_MODEL: str = Field(
        ..., min_length=1, description="Gemini model identifier"
    )
    FRONTEND_ORIGIN: str = Field(
        ...,
        min_length=1,
        description="Allowed frontend origin(s) for CORS, comma-separated",
    )
    BUCKET_MANAGER_URL: str = Field(
        ...,
        min_length=1,
        description="Internal URL of the bucket-manager microservice",
    )
    DOCUMENT_PROCESSOR_URL: str = Field(
        ...,
        min_length=1,
        description="Internal URL of the document-processor microservice",
    )
    INTERNAL_API_KEY: str = Field(
        ...,
        min_length=1,
        description="Shared secret key for internal service-to-service authentication",
    )
    INTERNAL_IAM_AUTH_ENABLED: bool = Field(
        default=False,
        description=(
            "Attach a Google Cloud Run ID token when calling bucket-manager and "
            "document-processor (required when they are deployed with "
            "--no-allow-unauthenticated)"
        ),
    )
    CHAT_RATE_LIMIT_PER_MINUTE: int = Field(
        default=20,
        ge=1,
        description="Maximum chat stream requests allowed per client IP per minute",
    )
    UPLOAD_RATE_LIMIT_PER_MINUTE: int = Field(
        default=10,
        ge=1,
        description="Maximum file upload requests allowed per client IP per minute",
    )
    DOWNLOAD_RATE_LIMIT_PER_MINUTE: int = Field(
        default=30,
        ge=1,
        description="Maximum file download requests allowed per client IP per minute",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return parsed list of allowed CORS origins."""
        origin_val = str(self.FRONTEND_ORIGIN)
        return [
            origin.strip()
            for origin in origin_val.split(",")
            if origin.strip()
        ]


settings = Settings()
