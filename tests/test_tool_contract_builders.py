"""Tests for framework.tool_contract_builders."""

from __future__ import annotations

import unittest

from framework.tool_action_observation_contract import (
    ToolActionRecord,
    ToolContractName,
    ToolContractStatus,
    ToolObservationRecord,
)
from framework.tool_contract_builders import (
    build_blocked_tool_observation,
    build_tool_action,
    build_tool_observation,
)


class ToolContractBuildersTest(unittest.TestCase):
    def test_build_tool_action_returns_record(self) -> None:
        a = build_tool_action(
            action_id="a1",
            session_id="s1",
            job_id="j1",
            tool_name=ToolContractName.SEARCH,
            arguments={"query": "foo"},
            requested_by="tester",
        )
        self.assertIsInstance(a, ToolActionRecord)
        self.assertEqual(a.tool_name, ToolContractName.SEARCH)
        self.assertEqual(a.arguments, {"query": "foo"})
        self.assertEqual(a.requested_by, "tester")

    def test_build_tool_action_default_arguments(self) -> None:
        a = build_tool_action(
            action_id="a2",
            session_id="s",
            job_id="j",
            tool_name=ToolContractName.READ_FILE,
        )
        self.assertEqual(a.arguments, {})
        self.assertEqual(a.requested_by, "phase2_entry")

    def test_build_tool_observation_ok(self) -> None:
        a = build_tool_action(
            action_id="a1",
            session_id="s1",
            job_id="j1",
            tool_name=ToolContractName.RUN_COMMAND,
        )
        obs = build_tool_observation(
            action=a,
            status=ToolContractStatus.EXECUTED,
            allowed=True,
            duration_ms=5,
            stdout="hello",
            structured_payload={"lines": 1},
            side_effect_metadata={"cwd": "/tmp"},
        )
        self.assertIsInstance(obs, ToolObservationRecord)
        self.assertTrue(obs.allowed)
        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        self.assertEqual(obs.action_id, "a1")
        self.assertEqual(obs.session_id, "s1")
        self.assertEqual(obs.job_id, "j1")
        self.assertEqual(obs.tool_name, ToolContractName.RUN_COMMAND)
        self.assertEqual(obs.structured_payload, {"lines": 1})
        self.assertEqual(obs.side_effect_metadata, {"cwd": "/tmp"})

    def test_build_blocked_tool_observation(self) -> None:
        a = build_tool_action(
            action_id="a1",
            session_id="s1",
            job_id="j1",
            tool_name=ToolContractName.APPLY_PATCH,
        )
        obs = build_blocked_tool_observation(action=a, reason="permission_denied")
        self.assertFalse(obs.allowed)
        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertEqual(obs.error, "permission_denied")
        self.assertEqual(obs.return_code, 126)
        d = obs.to_dict()
        self.assertEqual(d["status"], "blocked")
        self.assertEqual(d["allowed"], False)


if __name__ == "__main__":
    unittest.main()
