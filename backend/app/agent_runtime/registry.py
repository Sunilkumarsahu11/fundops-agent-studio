from collections.abc import Callable
from typing import Any

from .models import ToolDefinition, ToolResult

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    """Allow-listed deterministic tool registry with metadata."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if not definition.name.strip():
            raise ValueError("Tool name cannot be empty")
        self._tools[definition.name] = (definition, handler)

    def has(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str) -> ToolDefinition | None:
        item = self._tools.get(name)
        return item[0] if item else None

    def execute(self, name: str, inputs: dict[str, Any]) -> ToolResult:
        item = self._tools.get(name)
        if item is None:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        _, handler = item
        try:
            return ToolResult(success=True, output=handler(inputs))
        except Exception as exc:  # noqa: BLE001 - runtime boundary
            return ToolResult(success=False, error=str(exc))

    def definitions(self) -> list[ToolDefinition]:
        return [item[0] for item in self._tools.values()]

    def names(self) -> list[str]:
        return sorted(self._tools)
