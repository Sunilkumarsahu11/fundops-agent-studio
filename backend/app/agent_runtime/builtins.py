from typing import Any

from .models import ToolDefinition


def echo(inputs: dict[str, Any]) -> dict[str, Any]:
    return {"received": inputs}


def register_builtins(registry: Any) -> None:
    registry.register(
        ToolDefinition(
            name="echo",
            description="Reference deterministic tool used for smoke tests.",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        ),
        echo,
    )
