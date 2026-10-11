"""
Agent business logic service using LangChain and Gemini for GenChat
"""

import logging
from dataclasses import dataclass
from typing import AsyncGenerator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCall,
)
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from app.prompts.agent import get_system_prompt
from app.schemas.chat import (
    AgentStreamEvent,
    ChatHistoryMessage,
    ChatResponse,
    GeminiContentBlock,
    StreamActivityEvent,
    StreamCompleteEvent,
    StreamErrorEvent,
    StreamStatusEvent,
    StreamTokenEvent,
    StreamToolEndEvent,
    StreamToolStartEvent,
)
from app.services.document_service import DocumentService
from app.services.tool_executor import ToolExecutor, ExecutedToolResult, AgentServiceError
from app.tools.document_tools import create_document_tools

logger = logging.getLogger(__name__)


TOOL_ACTIVITY_CONFIG = {
    "convert_docx_to_pdf": {
        "id": "act-convert-docx-to-pdf",
        "started": "Converting DOCX to PDF...",
        "completed": "Converted DOCX to PDF",
    },
    "convert_pdf_to_docx": {
        "id": "act-convert-pdf-to-docx",
        "started": "Converting PDF to DOCX...",
        "completed": "Converted PDF to DOCX",
    },
}


@dataclass
class AgentChatContext:
    """Encapsulates the state and bound model required for an agent chat session."""

    tools: list[BaseTool]
    messages: list[BaseMessage]
    model: Runnable


class AgentService:
    """
    Modular Agent business logic service using LangChain and Gemini for GenChat
    """

    def __init__(
        self,
        model: BaseChatModel,
        tools: list[BaseTool] | None = None,
        document_service: DocumentService | None = None,
    ):
        self.model = model
        self.document_service = document_service
        self._custom_tools = tools

    def _build_tools(self) -> list[BaseTool]:
        """Build LangChain tools available to the agent."""
        if self._custom_tools is not None:
            return self._custom_tools
        if self.document_service is not None:
            return create_document_tools(self.document_service)
        return []

    @staticmethod
    def _build_initial_messages(
        user_message: str,
        history: list[ChatHistoryMessage] | None = None,
        attached_files: list[str] | None = None,
    ) -> list[BaseMessage]:
        """
        Build system prompt, sanitized conversation history, and current user message.
        """
        system_prompt = get_system_prompt()
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

        if history:
            sanitized_history = [h for h in history if h.content and h.content.strip()]
            truncated_history = sanitized_history[-10:]

            for item in truncated_history:
                cleaned_text = item.content.strip()
                if item.role == "user":
                    messages.append(HumanMessage(content=cleaned_text))
                elif item.role == "assistant":
                    messages.append(AIMessage(content=cleaned_text))

        full_user_content = user_message
        if attached_files and len(attached_files) > 0:
            files_note = f"\n[Attached Files: {', '.join(attached_files)}]"
            full_user_content += files_note

        messages.append(HumanMessage(content=full_user_content))
        return messages

    def _prepare_context(
        self,
        user_message: str,
        history: list[ChatHistoryMessage] | None = None,
        attached_files: list[str] | None = None,
    ) -> AgentChatContext:
        """Prepare tools, messages, and tool-bound model for a chat session."""
        tools = self._build_tools()
        messages = self._build_initial_messages(user_message, history, attached_files)
        bound_model = self.model.bind_tools(tools) if tools else self.model
        return AgentChatContext(tools=tools, messages=messages, model=bound_model)

    @staticmethod
    def _extract_message_text(message: AIMessage) -> str:
        """Extract text content from LangChain AIMessage."""
        content = message.content

        if isinstance(content, str):
            return content

        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
                continue

            block = GeminiContentBlock.model_validate(part)
            parts.append(block.text)

        return "".join(parts)

    @classmethod
    def _extract_chunk_text(cls, chunk: BaseMessage) -> str:
        """Extract text from a streamed LangChain message chunk."""
        if not isinstance(chunk, AIMessage):
            return ""
        return cls._extract_message_text(chunk)

    @classmethod
    def _get_activity_id(cls, tool_name: str, turn: int) -> str:
        """Get canonical activity ID matching TOOL_ACTIVITY_CONFIG."""
        config = TOOL_ACTIVITY_CONFIG.get(tool_name)
        base_id = config["id"] if config else f"act-{tool_name}"
        return base_id if turn == 0 else f"{base_id}-turn-{turn}"

    @classmethod
    def _build_started_activity_message(
        cls, tool_name: str, tool_calls: list[ToolCall]
    ) -> str:
        config = TOOL_ACTIVITY_CONFIG.get(tool_name)
        if config:
            return config["started"]
        human_name = tool_name.replace("_", " ").title()
        return f"Executing {human_name}..."

    @classmethod
    def _build_completed_activity_message(
        cls, tool_name: str, results: list[ExecutedToolResult]
    ) -> str:
        config = TOOL_ACTIVITY_CONFIG.get(tool_name)
        if config:
            return config["completed"]
        human_name = tool_name.replace("_", " ").title()
        return f"Completed {human_name}"

    async def chat(
        self,
        user_message: str,
        history: list[ChatHistoryMessage] | None = None,
        attached_files: list[str] | None = None,
    ) -> ChatResponse:
        """Process user message synchronously via LangChain."""
        ctx = self._prepare_context(user_message, history, attached_files)
        tool_executor = ToolExecutor(ctx.tools)
        max_tool_turns = 5

        try:
            response: AIMessage | None = None
            has_finished_text_turn = False
            for _ in range(max_tool_turns):
                response = await ctx.model.ainvoke(ctx.messages)
                if not isinstance(response, AIMessage) or not response.tool_calls:
                    has_finished_text_turn = True
                    break
                ctx.messages.append(response)
                await tool_executor.execute(response.tool_calls, ctx.messages)

            if not has_finished_text_turn:
                response = await self.model.ainvoke(ctx.messages)

            if response is None or not isinstance(response, AIMessage):
                raise AgentServiceError("Failed to generate AI response.")

            text_content = self._extract_message_text(response)
            return ChatResponse(message=text_content)
        except Exception as e:
            logger.exception("Error invoking model in AgentService: %s", str(e))
            raise AgentServiceError("Failed to generate AI response.") from e

    async def stream_chat(
        self,
        user_message: str,
        history: list[ChatHistoryMessage] | None = None,
        attached_files: list[str] | None = None,
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Process user message via LangChain, streaming typed SSE events with real-time sequential activities."""
        try:
            yield StreamStatusEvent(
                status="analyzing", message="Analyzing your request..."
            )
            yield StreamActivityEvent(
                id="act-understanding",
                message="Understanding your request",
                status="started",
            )

            ctx = self._prepare_context(user_message, history, attached_files)
            tool_executor = ToolExecutor(ctx.tools)
            max_tool_turns = 5
            has_finished_text_turn = False

            for turn in range(max_tool_turns):
                current_ai_message: AIMessage | None = None

                async for event in ctx.model.astream_events(ctx.messages, version="v2"):
                    if event["event"] == "on_chat_model_stream":
                        token_text = self._extract_chunk_text(event["data"]["chunk"])
                        if token_text:
                            yield StreamTokenEvent(token=token_text)
                    elif event["event"] == "on_chat_model_end":
                        output = event["data"]["output"]
                        if isinstance(output, AIMessage):
                            current_ai_message = output

                if turn == 0:
                    yield StreamActivityEvent(
                        id="act-understanding",
                        message="Understood your request",
                        status="completed",
                    )

                if not current_ai_message or not current_ai_message.tool_calls:
                    has_finished_text_turn = True
                    break

                # Phase 2: Sequential Tool Execution
                yield StreamStatusEvent(
                    status="executing_tools",
                    message="Executing requested action...",
                )
                ctx.messages.append(current_ai_message)

                # Group tool calls by tool_name in current turn
                grouped_tool_calls: dict[str, list[ToolCall]] = {}
                for tc in current_ai_message.tool_calls:
                    grouped_tool_calls.setdefault(tc["name"], []).append(tc)

                # Sequentially process each tool group: emit started, execute, emit completed
                for tool_name, calls in grouped_tool_calls.items():
                    activity_id = self._get_activity_id(tool_name, turn)
                    started_message = self._build_started_activity_message(
                        tool_name, calls
                    )

                    # 1. Emit started activity event for active group right before execution
                    yield StreamActivityEvent(
                        id=activity_id,
                        message=started_message,
                        status="started",
                    )

                    # 2. Emit tool start events for calls in active group
                    for tc in calls:
                        yield StreamToolStartEvent(tool_name=tc["name"])

                    # 3. Execute calls for active tool group
                    executed_results = await tool_executor.execute(
                        calls, ctx.messages
                    )

                    # 4. Emit tool end events for calls in active group
                    for tc in calls:
                        yield StreamToolEndEvent(tool_name=tc["name"])

                    # 5. Emit completed activity event for active group upon completion
                    completed_message = self._build_completed_activity_message(
                        tool_name, executed_results
                    )
                    yield StreamActivityEvent(
                        id=activity_id,
                        message=completed_message,
                        status="completed",
                    )

            if not has_finished_text_turn:
                async for event in self.model.astream_events(
                    ctx.messages, version="v2"
                ):
                    if event["event"] == "on_chat_model_stream":
                        token_text = self._extract_chunk_text(event["data"]["chunk"])
                        if token_text:
                            yield StreamTokenEvent(token=token_text)

            yield StreamCompleteEvent()

        except Exception as e:
            logger.exception("Error in stream_chat: %s", str(e))
            yield StreamErrorEvent(
                error="Failed to generate AI response. Please try again later."
            )
