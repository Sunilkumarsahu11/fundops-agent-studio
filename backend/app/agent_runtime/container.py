from .builtins import register_builtins
from .registry import ToolRegistry

registry = ToolRegistry()
register_builtins(registry)
