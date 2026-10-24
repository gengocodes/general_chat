"""Configuration settings for the Document-Processor microservice."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings loaded from environment or .env file."""

    INTERNAL_API_KEY: str = Field(
        ...,
        min_length=1,
        description="Shared secret key for internal service-to-service authentication",
    )
    BUCKET_MANAGER_URL: str = Field(
        ...,
        min_length=1,
        description="Internal URL of the bucket-manager microservice",
    )
    INTERNAL_IAM_AUTH_ENABLED: bool = Field(
        default=False,
        description=(
            "Attach a Google Cloud Run ID token when calling bucket-manager "
            "(required when bucket-manager is deployed with --no-allow-unauthenticated)"
        ),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
