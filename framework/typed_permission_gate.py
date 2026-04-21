"""Allow/ask/deny permission gate for tool_schema.ToolAction typed surface."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from framework.tool_bridge import is_schema_action, tool_name_for
from framework.tool_schema import RunCommandAction


class ToolPermission(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass(frozen=True)
class PermissionRule:
    tool_name: str
    permission: ToolPermission
    command_pattern: Optional[str] = None


@dataclass
class TypedPermissionGate:
    rules: list = field(default_factory=list)
    default_permission: ToolPermission = ToolPermission.DENY

    def evaluate(self, action: object) -> ToolPermission:
        if not is_schema_action(action):
            raise TypeError(
                f"TypedPermissionGate requires a tool_schema.ToolAction; got {type(action)!r}"
            )
        name = tool_name_for(action)
        cmd_str = action.command if isinstance(action, RunCommandAction) else None

        for rule in self.rules:
            if rule.tool_name != "*" and rule.tool_name != name:
                continue
            if rule.command_pattern is not None:
                if cmd_str is None:
                    continue
                if not re.search(rule.command_pattern, cmd_str):
                    continue
            return rule.permission

        return self.default_permission

    def is_allowed(self, action: object) -> bool:
        return self.evaluate(action) == ToolPermission.ALLOW


__all__ = ["PermissionRule", "ToolPermission", "TypedPermissionGate"]
