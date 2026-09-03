from collections.abc import Callable
from typing import Any

from .models import ToolResult

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    """Registry of deterministic tools available to agents."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        if not name.strip():
            raise ValueError("Tool name cannot be empty")
        self._tools[name] = handler

    def has(self, name: str) -> bool:
        return name in self._tools

    def execute(self, name: str, inputs: dict[str, Any]) -> ToolResult:
        handler = self._tools.get(name)
        if handler is None:
            return ToolResult(success=False, error=f"Unknown tool: {name}")

        try:
            return ToolResult(success=True, output=handler(inputs))
        except Exception as exc:  # noqa: BLE001 - runtime boundary
            return ToolResult(success=False, error=str(exc))

    def names(self) -> list[str]:
        return sorted(self._tools)
