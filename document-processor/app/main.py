"""Main FastAPI application entry point for Document-Processor."""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.infrastructure.logging import setup_logging
from app.presentation.routers import conversions

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GenChat Document-Processor",
    description="Internal document conversion microservice (DOCX <-> PDF)",
    version="1.0.0",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled server errors and avoid leaking internal stack traces."""
    logger.exception(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(conversions.router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Liveness and readiness probe endpoint."""
    return {"status": "healthy", "service": "genchat-document-processor"}
