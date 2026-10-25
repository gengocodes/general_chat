"""
FastAPI application entry point for GenChat - Paul Corsino's AI Assistant API
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.infrastructure.logging import setup_logging
from app.presentation.routers import chat, upload

setup_logging()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    app: str


app = FastAPI(
    title="GenChat API",
    description=(
        "Paul Corsino's general AI chat assistant API "
        "with streaming SSE and tool execution"
    ),
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint returning application status."""
    return HealthResponse(status="ok", app="GenChat")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler logging unhandled server errors."""
    logger.exception(
        "Unhandled server error: %s %s - %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
