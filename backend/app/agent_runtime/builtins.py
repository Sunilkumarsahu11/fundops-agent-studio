from typing import Any


def echo(inputs: dict[str, Any]) -> dict[str, Any]:
    """Reference deterministic tool used by runtime tests and smoke runs."""
    return {"received": inputs}
