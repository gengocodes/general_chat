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
