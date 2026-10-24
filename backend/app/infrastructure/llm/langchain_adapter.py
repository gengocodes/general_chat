"""
LangChainChatAdapter implementing ChatModelPort
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
import logging
from typing import AsyncGenerator
from pydantic import BaseModel, ConfigDict
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

from app.domain.entities.message import ChatMessage
from app.domain.events import (
    AgentStreamEvent,
    StreamActivityEvent,
    StreamCompleteEvent,
    StreamErrorEvent,
    StreamTokenEvent,
)
from app.application.ports.chat_model_port import ChatModelPort
from app.infrastructure.llm.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class GeminiContentBlock(BaseModel):
    """Structured content block returned by Gemini through LangChain AIMessage."""

    model_config = ConfigDict(extra="ignore")

    type: str
    text: str


@dataclass
class AgentChatContext:
    """Encapsulates the state and bound model required for an agent chat session."""

    tools: list[BaseTool]
    messages: list[BaseMessage]
    model: Runnable


@dataclass(frozen=True)
class ToolCallGroup:
    """Batch of tool calls sharing the same tool name within a single model turn."""

    tool_name: str
    calls: list[ToolCall]


@dataclass
class _TurnStreamCollector:
    """Mutable collector tracking the final AIMessage emitted during a streamed model turn."""

    ai_message: AIMessage | None = field(default=None)


class LangChainChatAdapter(ChatModelPort):  # pylint: disable=too-few-public-methods
    """ChatModelPort implementation wrapping LangChain chat models and tool execution."""

    MAX_TOOL_TURNS: int = 5

    def __init__(
        self,
        model: BaseChatModel,
        tools: Sequence[BaseTool] = (),
    ):
        self.model = model
        self.tools = list(tools)

    @staticmethod
    def _to_langchain_messages(
        system_prompt: str,
        user_message: str,
        history: Sequence[ChatMessage],
    ) -> list[BaseMessage]:
        """Convert domain prompt and history entities into LangChain message objects."""
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        for item in history:
            if item.role == "user":
                messages.append(HumanMessage(content=item.content))
            elif item.role == "assistant":
                messages.append(AIMessage(content=item.content))
        messages.append(HumanMessage(content=user_message))
        return messages

    def _prepare_context(
        self,
        system_prompt: str,
        user_message: str,
        history: Sequence[ChatMessage],
    ) -> AgentChatContext:
        messages = self._to_langchain_messages(system_prompt, user_message, history)
        bound_model = self.model.bind_tools(self.tools) if self.tools else self.model
        return AgentChatContext(tools=self.tools, messages=messages, model=bound_model)

    @staticmethod
    def _extract_message_text(message: AIMessage) -> str:
        content = message.content
        if isinstance(content, str):
            return content

        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            else:
                block = GeminiContentBlock.model_validate(part)
                parts.append(block.text)
        return "".join(parts)

    @classmethod
    def _extract_chunk_text(cls, chunk: BaseMessage) -> str:
        if not isinstance(chunk, AIMessage):
            return ""
        return cls._extract_message_text(chunk)

    @staticmethod
    def _get_activity_id(tool_name: str, turn: int) -> str:
        base_id = f"act-{tool_name.replace('_', '-')}"
        return base_id if turn == 0 else f"{base_id}-turn-{turn}"

    @staticmethod
    def _format_tool_title(tool_name: str) -> str:
        return tool_name.replace("_", " ").title()

    @staticmethod
    def _group_tool_calls(tool_calls: Sequence[ToolCall]) -> list[ToolCallGroup]:
        grouped: dict[str, list[ToolCall]] = {}
        for tc in tool_calls:
            grouped.setdefault(tc["name"], []).append(tc)
        return [
            ToolCallGroup(tool_name=name, calls=calls)
            for name, calls in grouped.items()
        ]

    async def _stream_model_turn(
        self,
        model: Runnable,
        messages: list[BaseMessage],
        collector: _TurnStreamCollector,
    ) -> AsyncGenerator[StreamTokenEvent, None]:
        """Stream token events for a single model invocation and record the final AIMessage."""
        async for event in model.astream_events(messages, version="v2"):
            if event["event"] == "on_chat_model_stream":
                token_text = self._extract_chunk_text(event["data"]["chunk"])
                if token_text:
                    yield StreamTokenEvent(token=token_text)
            elif event["event"] == "on_chat_model_end":
                output = event["data"]["output"]
                if isinstance(output, AIMessage):
                    collector.ai_message = output

    async def _execute_tool_group_stream(
        self,
        group: ToolCallGroup,
        turn: int,
        tool_executor: ToolExecutor,
        messages: list[BaseMessage],
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Execute a group of tool calls and yield corresponding activity lifecycle events."""
        activity_id = self._get_activity_id(group.tool_name, turn)
        human_name = self._format_tool_title(group.tool_name)

        yield StreamActivityEvent(
            id=activity_id,
            message=f"Executing {human_name}...",
            status="started",
        )

        await tool_executor.execute(group.calls, messages)

        yield StreamActivityEvent(
            id=activity_id,
            message=f"Completed {human_name}",
            status="completed",
        )

    async def _run_streaming_turns(
        self, ctx: AgentChatContext, tool_executor: ToolExecutor
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Run up to MAX_TOOL_TURNS of streaming model generation and tool execution."""
        has_finished_text_turn = False

        for turn in range(self.MAX_TOOL_TURNS):
            collector = _TurnStreamCollector()
            async for token_event in self._stream_model_turn(
                ctx.model, ctx.messages, collector
            ):
                yield token_event

            if turn == 0:
                yield StreamActivityEvent(
                    id="act-understanding",
                    message="Understood your request",
                    status="completed",
                )

            current_ai_message = collector.ai_message
            if not current_ai_message or not current_ai_message.tool_calls:
                has_finished_text_turn = True
                break

            ctx.messages.append(current_ai_message)

            for group in self._group_tool_calls(current_ai_message.tool_calls):
                async for tool_event in self._execute_tool_group_stream(
                    group, turn, tool_executor, ctx.messages
                ):
                    yield tool_event

        if not has_finished_text_turn:
            async for token_event in self._stream_model_turn(
                self.model, ctx.messages, _TurnStreamCollector()
            ):
                yield token_event

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        history: Sequence[ChatMessage] = (),
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        try:
            yield StreamActivityEvent(
                id="act-understanding",
                message="Understanding your request",
                status="started",
            )

            ctx = self._prepare_context(system_prompt, user_message, history)
            tool_executor = ToolExecutor(ctx.tools)

            async for event in self._run_streaming_turns(ctx, tool_executor):
                yield event

            yield StreamCompleteEvent()

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Error in stream_chat: %s", str(e))
            yield StreamErrorEvent(
                error="Failed to generate AI response. Please try again later."
            )
