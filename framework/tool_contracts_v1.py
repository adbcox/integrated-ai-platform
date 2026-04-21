"""Typed tool contracts for the minimum substrate (Phase 2, P2-01)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ToolContractV1:
    tool_name: str
    action_fields: List[str]
    observation_fields: List[str]
    side_effecting: bool


READ_FILE = ToolContractV1(
    tool_name="read_file",
    action_fields=["path", "offset", "limit"],
    observation_fields=["content", "line_count", "truncated"],
    side_effecting=False,
)

RUN_COMMAND = ToolContractV1(
    tool_name="run_command",
    action_fields=["command", "category", "timeout_override", "cwd"],
    observation_fields=["status", "stdout", "stderr", "exit_code", "duration_ms"],
    side_effecting=True,
)

RUN_TESTS = ToolContractV1(
    tool_name="run_tests",
    action_fields=["test_path", "timeout_override", "extra_args"],
    observation_fields=["status", "passed", "failed", "errors", "stdout", "duration_ms"],
    side_effecting=False,
)

PUBLISH_ARTIFACT = ToolContractV1(
    tool_name="publish_artifact",
    action_fields=["artifact_path", "artifact_id", "content"],
    observation_fields=["written", "artifact_path", "byte_count"],
    side_effecting=True,
)

ALL_CONTRACTS: List[ToolContractV1] = [READ_FILE, RUN_COMMAND, RUN_TESTS, PUBLISH_ARTIFACT]
