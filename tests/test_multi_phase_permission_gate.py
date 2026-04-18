from __future__ import annotations

import unittest

from framework.multi_phase_permission_gate import (
    gate_multi_phase_action,
    gate_multi_phase_tool_name,
)
from framework.permission_engine import PermissionEngine
from framework.tool_system import ToolAction, ToolName, ToolStatus


class MultiPhasePermissionGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PermissionEngine()

    def test_allows_inference_when_declared(self) -> None:
        action = ToolAction(
            job_id="mc-seed-allow",
            tool=ToolName.INFERENCE,
            arguments={},
        )
        obs = gate_multi_phase_action(
            action=action,
            engine=self.engine,
            allowed_tools=["inference"],
        )
        self.assertTrue(obs.allowed)
        self.assertEqual(obs.status, ToolStatus.ALLOWED)
        self.assertEqual(obs.tool, ToolName.INFERENCE)
        self.assertEqual(obs.job_id, "mc-seed-allow")
        self.assertEqual(obs.metadata["multi_phase_gate"], "v1")
        self.assertTrue(obs.metadata["permission_decision"]["allowed"])

    def test_blocks_tool_not_allowed_for_job(self) -> None:
        action = ToolAction(
            job_id="mc-seed-wrong-tool",
            tool=ToolName.APPLY_EDIT,
            arguments={"path": "framework/scratch.py"},
        )
        obs = gate_multi_phase_action(
            action=action,
            engine=self.engine,
            allowed_tools=["inference"],
        )
        self.assertFalse(obs.allowed)
        self.assertEqual(obs.status, ToolStatus.BLOCKED)
        self.assertEqual(obs.error, "tool_not_allowed_for_job")

    def test_blocks_dangerous_substring(self) -> None:
        action = ToolAction(
            job_id="mc-seed-dangerous",
            tool=ToolName.RUN_COMMAND,
            arguments={"command": "rm -rf /"},
        )
        obs = gate_multi_phase_action(
            action=action,
            engine=self.engine,
            allowed_tools=["run_command"],
        )
        self.assertFalse(obs.allowed)
        self.assertEqual(obs.status, ToolStatus.BLOCKED)
        self.assertEqual(obs.error, "blocked_dangerous_substring")

    def test_allows_safe_run_command(self) -> None:
        action = ToolAction(
            job_id="mc-seed-safe",
            tool=ToolName.RUN_COMMAND,
            arguments={"command": "echo hello"},
        )
        obs = gate_multi_phase_action(
            action=action,
            engine=self.engine,
            allowed_tools=["run_command"],
        )
        self.assertTrue(obs.allowed)
        self.assertEqual(obs.status, ToolStatus.ALLOWED)

    def test_missing_command_is_blocked(self) -> None:
        action = ToolAction(
            job_id="mc-seed-missing-cmd",
            tool=ToolName.RUN_COMMAND,
            arguments={"command": ""},
        )
        obs = gate_multi_phase_action(
            action=action,
            engine=self.engine,
            allowed_tools=["run_command"],
        )
        self.assertFalse(obs.allowed)
        self.assertEqual(obs.error, "missing_command")

    def test_tool_name_wrapper_builds_action(self) -> None:
        obs = gate_multi_phase_tool_name(
            job_id="mc-seed-wrap",
            tool_name=ToolName.INFERENCE,
            arguments={},
            engine=self.engine,
            allowed_tools=["inference"],
        )
        self.assertTrue(obs.allowed)
        self.assertEqual(obs.tool, ToolName.INFERENCE)
        self.assertEqual(obs.job_id, "mc-seed-wrap")

    def test_type_errors_for_wrong_action_type(self) -> None:
        with self.assertRaises(TypeError):
            gate_multi_phase_action(
                action={"tool": "inference"},
                engine=self.engine,
                allowed_tools=["inference"],
            )

    def test_type_errors_for_wrong_engine_type(self) -> None:
        action = ToolAction(
            job_id="mc-seed-bad-engine",
            tool=ToolName.INFERENCE,
        )
        with self.assertRaises(TypeError):
            gate_multi_phase_action(
                action=action,
                engine=object(),
                allowed_tools=["inference"],
            )


if __name__ == "__main__":
    unittest.main()
