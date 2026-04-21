"""Bridge between framework.tool_system (legacy 4-tool surface) and
framework.tool_schema (typed 9-tool contract surface).

- SCHEMA_TOOL_NAMES: frozenset of canonical tool name strings
- is_schema_action(obj): True if obj is an instance of tool_schema.ToolAction
- tool_name_for(action): string tool name for a schema action instance

Stdlib-only except for tool_schema import. Does not import from tool_system.
"""
from __future__ import annotations

from framework.tool_schema import TOOL_ACTION_TYPES
from framework.tool_schema import ToolAction as _SchemaBase

SCHEMA_TOOL_NAMES: frozenset = frozenset(TOOL_ACTION_TYPES.keys())


def is_schema_action(obj: object) -> bool:
    """Return True if obj is an instance of the tool_schema.ToolAction hierarchy."""
    return isinstance(obj, _SchemaBase)


def tool_name_for(action: object) -> str:
    """Return the canonical tool name string for a typed schema action.

    Raises TypeError for non-schema-action objects.
    Raises ValueError for unregistered schema action subclasses.
    """
    if not isinstance(action, _SchemaBase):
        raise TypeError(
            f"Expected a tool_schema.ToolAction subclass; got {type(action)!r}"
        )
    cls = type(action)
    for name, registered_cls in TOOL_ACTION_TYPES.items():
        if cls is registered_cls:
            return name
    raise ValueError(f"Action class {cls!r} is not registered in TOOL_ACTION_TYPES")


__all__ = ["SCHEMA_TOOL_NAMES", "is_schema_action", "tool_name_for"]
