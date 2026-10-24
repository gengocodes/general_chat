"""
ToolExecutor service for executing and deduplicating LangChain tools.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from langchain_core.messages import BaseMessage, ToolCall, ToolMessage
from langchain_core.tools import BaseTool

from app.domain.tools import AgentToolResult
from app.domain.errors import AgentServiceError


@dataclass(frozen=True)
class ToolCacheKey:
    """Hashable key identifying a tool invocation by name and serialized arguments."""

    tool_name: str
    serialized_args: str


@dataclass(frozen=True)
class ExecutedToolResult:
    """Structured representation of an executed tool call."""

    tool_call_id: str
    tool_name: str
    tool_args: dict[str, Any]
    raw_result: Any
    success: bool
    error_message: str | None
    tool_message: ToolMessage


class ToolExecutor:  # pylint: disable=too-few-public-methods
    """Lightweight executor for looking up, deduplicating, and executing LangChain tools."""

    def __init__(self, tools: Sequence[BaseTool]):
        self.tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}

    @staticmethod
    def _build_cache_key(tool_name: str, tool_args: dict[str, Any]) -> ToolCacheKey:
        """Build a deterministic cache key for deduplicating identical tool calls."""
        return ToolCacheKey(
            tool_name=tool_name,
            serialized_args=str(sorted(tool_args.items())),
        )

    @staticmethod
    def _clone_cached_result(
        cached: ExecutedToolResult,
        tool_call_id: str,
        tool_args: dict[str, Any],
    ) -> ExecutedToolResult:
        """Create a new ExecutedToolResult bound to the current tool_call_id from a cached run."""
        tool_message = ToolMessage(
            content=cached.tool_message.content,
            tool_call_id=tool_call_id,
        )
        return ExecutedToolResult(
            tool_call_id=tool_call_id,
            tool_name=cached.tool_name,
            tool_args=tool_args,
            raw_result=cached.raw_result,
            success=cached.success,
            error_message=cached.error_message,
            tool_message=tool_message,
        )

    @staticmethod
    def _build_unknown_tool_result(
        tool_name: str,
        tool_args: dict[str, Any],
        tool_call_id: str,
    ) -> ExecutedToolResult:
        """Build an error ExecutedToolResult when the requested tool is not registered."""
        error_msg = f"Unknown tool '{tool_name}'."
        tool_message = ToolMessage(
            content=error_msg,
            tool_call_id=tool_call_id,
        )
        return ExecutedToolResult(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_args=tool_args,
            raw_result=None,
            success=False,
            error_message=error_msg,
            tool_message=tool_message,
        )

    @staticmethod
    async def _invoke_single_tool(
        selected_tool: BaseTool,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_call_id: str,
    ) -> ExecutedToolResult:
        """Invoke a single LangChain tool and return its structured result and ToolMessage."""
        raw_result: Any = None
        success = False
        error_message: str | None = None

        try:
            raw_result = await selected_tool.ainvoke(tool_args)
            if isinstance(raw_result, AgentToolResult):
                success = raw_result.success
                error_message = raw_result.message if not success else None
            else:
                success = True
            tool_msg_content = str(raw_result)
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_message = str(e)
            tool_msg_content = f"Error executing tool '{tool_name}': {e}"

        tool_message = ToolMessage(
            content=tool_msg_content,
            tool_call_id=tool_call_id,
        )
        return ExecutedToolResult(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_args=tool_args,
            raw_result=raw_result,
            success=success,
            error_message=error_message,
            tool_message=tool_message,
        )

    async def execute(
        self, tool_calls: Sequence[ToolCall], messages: list[BaseMessage]
    ) -> list[ExecutedToolResult]:
        """
        Execute requested tools sequentially, append ToolMessages to messages,
        and return typed results.
        """
        executed_results: dict[ToolCacheKey, ExecutedToolResult] = {}
        results: list[ExecutedToolResult] = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id")
            if tool_id is None:
                raise AgentServiceError("Tool call missing ID.")

            selected_tool = self.tools_by_name.get(tool_name)
            if selected_tool is None:
                unknown_res = self._build_unknown_tool_result(
                    tool_name, tool_args, tool_id
                )
                messages.append(unknown_res.tool_message)
                results.append(unknown_res)
                continue

            cache_key = self._build_cache_key(tool_name, tool_args)
            if cache_key in executed_results:
                cloned = self._clone_cached_result(
                    executed_results[cache_key], tool_id, tool_args
                )
                messages.append(cloned.tool_message)
                results.append(cloned)
                continue

            exec_res = await self._invoke_single_tool(
                selected_tool, tool_name, tool_args, tool_id
            )
            messages.append(exec_res.tool_message)
            executed_results[cache_key] = exec_res
            results.append(exec_res)

        return results
