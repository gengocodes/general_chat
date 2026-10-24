"""FastAPI entrypoint for GenChat Bucket-Manager microservice."""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.infrastructure.logging import setup_logging
from app.presentation.routers import objects

setup_logging()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str


app = FastAPI(
    title="GenChat Bucket-Manager API",
    description="Internal Cloudflare R2 object storage and presigned URL microservice",
    version="1.0.0",
)

app.include_router(objects.router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint returning service status."""
    return HealthResponse(status="ok", service="bucket-manager")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler logging unhandled server errors."""
    logger.exception(
        "Unhandled server error in bucket-manager: %s %s - %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
