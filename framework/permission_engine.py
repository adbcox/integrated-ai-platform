"""Permission policy engine for framework tool execution."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Any

from .tool_system import ToolAction, ToolName


_BLOCKED_SUBSTRINGS = (
    "rm -rf /",
    "mkfs",
    "shutdown",
    "reboot",
    "poweroff",
)


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str
    matched_rule: str = ""
    evaluated_segments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "matched_rule": self.matched_rule,
            "evaluated_segments": list(self.evaluated_segments),
        }


class PermissionEngine:
    """Evaluates allow/deny rules for tool invocations."""

    def __init__(self, *, default_allow_tools: set[str] | None = None) -> None:
        self.default_allow_tools = default_allow_tools or {ToolName.INFERENCE.value, ToolName.RUN_COMMAND.value, ToolName.RUN_TESTS.value}

    def evaluate(self, *, action: ToolAction, allowed_tools_actions: list[str], metadata: dict[str, Any]) -> PermissionDecision:
        declared = self._normalize_declared_tools(allowed_tools_actions) if allowed_tools_actions else set(self.default_allow_tools)
        if action.tool.value not in declared:
            return PermissionDecision(False, "tool_not_allowed_for_job")

        policy = metadata.get("permission_policy") if isinstance(metadata.get("permission_policy"), dict) else {}
        deny_patterns = [str(x) for x in (policy.get("deny_command_patterns") or [])]
        allow_patterns = [str(x) for x in (policy.get("allow_command_patterns") or [])]

        if action.tool in {ToolName.RUN_COMMAND, ToolName.RUN_TESTS}:
            command = str(action.arguments.get("command") or "").strip()
            if not command:
                return PermissionDecision(False, "missing_command")
            lowered = command.lower()
            for token in _BLOCKED_SUBSTRINGS:
                if token in lowered:
                    return PermissionDecision(False, "blocked_dangerous_substring", matched_rule=token)

            segments = self._split_compound_command(command)
            for segment in segments:
                if self._segment_matches(deny_patterns, segment):
                    return PermissionDecision(
                        False,
                        "denied_by_pattern",
                        matched_rule=self._first_match(deny_patterns, segment),
                        evaluated_segments=segments,
                    )
            if allow_patterns:
                for segment in segments:
                    if not self._segment_matches(allow_patterns, segment):
                        return PermissionDecision(
                            False,
                            "not_in_allow_patterns",
                            evaluated_segments=segments,
                        )
            return PermissionDecision(True, "allowed", evaluated_segments=segments)

        return PermissionDecision(True, "allowed")

    def _normalize_declared_tools(self, allowed_tools_actions: list[str]) -> set[str]:
        alias_map = {
            "shell_command": ToolName.RUN_COMMAND.value,
            "shell": ToolName.RUN_COMMAND.value,
            "inference_only": ToolName.INFERENCE.value,
            "inference": ToolName.INFERENCE.value,
            "run_tests": ToolName.RUN_TESTS.value,
            "validation": ToolName.RUN_TESTS.value,
        }
        normalized: set[str] = set()
        for raw in allowed_tools_actions:
            value = str(raw).strip().lower()
            if not value:
                continue
            normalized.add(alias_map.get(value, value))
        return normalized

    def _segment_matches(self, patterns: list[str], segment: str) -> bool:
        for pattern in patterns:
            if re.search(pattern, segment):
                return True
        return False

    def _first_match(self, patterns: list[str], segment: str) -> str:
        for pattern in patterns:
            if re.search(pattern, segment):
                return pattern
        return ""

    def _split_compound_command(self, command: str) -> list[str]:
        # Normalize typical shell chaining operators so policy applies per subcommand.
        normalized = re.sub(r"\s*(\|\||&&|\||;)\s*", " ; ", command)
        try:
            tokens = shlex.split(normalized)
        except ValueError:
            return [command.strip()]
        segments: list[str] = []
        current: list[str] = []
        for token in tokens:
            if token == ";":
                if current:
                    segments.append(" ".join(current).strip())
                    current = []
                continue
            current.append(token)
        if current:
            segments.append(" ".join(current).strip())
        return [segment for segment in segments if segment]
