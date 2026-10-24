"""
Composition Root: Dependency wiring for FastAPI
"""

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.application.use_cases.chat import StreamChatMessageUseCase
from app.application.use_cases.file import (
    UploadFileUseCase,
    GetFileDownloadUseCase,
)
from app.infrastructure.storage.bucket_manager_adapter import (
    BucketManagerStorageAdapter,
)
from app.infrastructure.document.document_processor_adapter import (
    DocumentProcessorHttpAdapter,
)
from app.infrastructure.llm.document_tools import create_document_tools
from app.infrastructure.llm.langchain_adapter import LangChainChatAdapter

# Singletons / reusable infrastructure instances
_storage_adapter = BucketManagerStorageAdapter(
    base_url=settings.BUCKET_MANAGER_URL,
    internal_api_key=settings.INTERNAL_API_KEY,
)
_document_processor = DocumentProcessorHttpAdapter(
    base_url=settings.DOCUMENT_PROCESSOR_URL,
    internal_api_key=settings.INTERNAL_API_KEY,
)
_document_tools = create_document_tools(document_processor=_document_processor)


def get_chat_model_adapter() -> LangChainChatAdapter:
    """Creates LangChainChatAdapter bound to Google Gemini model and tools."""
    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )
    return LangChainChatAdapter(model=model, tools=_document_tools)


def get_stream_chat_use_case() -> StreamChatMessageUseCase:
    """Provides StreamChatMessageUseCase wired with ChatModelPort adapter."""
    chat_model = get_chat_model_adapter()
    return StreamChatMessageUseCase(chat_model=chat_model)


def get_upload_file_use_case() -> UploadFileUseCase:
    """Provides UploadFileUseCase wired with FileStoragePort adapter."""
    return UploadFileUseCase(storage=_storage_adapter)


def get_file_download_use_case() -> GetFileDownloadUseCase:
    """Provides GetFileDownloadUseCase wired with FileStoragePort adapter."""
    return GetFileDownloadUseCase(storage=_storage_adapter)
