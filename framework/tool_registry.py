"""Tool contract registry mapping tool names to their typed contract entries.

Imports only from framework.tool_schema. No other framework module imports.

Format contract: governance/tool_contract_spec.json
Schema version:  1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from framework.tool_schema import (
    TOOL_ACTION_TYPES,
    TOOL_OBSERVATION_TYPES,
    ToolAction,
    ToolObservation,
)


@dataclass(frozen=True)
class ToolContractEntry:
    name: str
    action_type: type
    observation_type: type


class ToolRegistry:
    """Registry mapping tool names to their typed contract entries."""

    def __init__(self) -> None:
        self._entries: dict[str, ToolContractEntry] = {}

    def register(self, entry: ToolContractEntry) -> None:
        self._entries[entry.name] = entry

    def get(self, name: str) -> Optional[ToolContractEntry]:
        return self._entries.get(name)

    def list_tools(self) -> list[str]:
        return sorted(self._entries.keys())

    def __len__(self) -> int:
        return len(self._entries)


def _build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for name, action_cls in TOOL_ACTION_TYPES.items():
        observation_cls = TOOL_OBSERVATION_TYPES[name]
        registry.register(ToolContractEntry(
            name=name,
            action_type=action_cls,
            observation_type=observation_cls,
        ))
    return registry


DEFAULT_REGISTRY: ToolRegistry = _build_default_registry()

__all__ = [
    "ToolContractEntry",
    "ToolRegistry",
    "DEFAULT_REGISTRY",
]
