"""Tests for framework.tool_action_observation_contract."""

from __future__ import annotations

import unittest

from framework.tool_action_observation_contract import (
    ToolActionRecord,
    ToolContractName,
    ToolContractStatus,
    ToolObservationRecord,
)


REQUIRED_TOOL_MEMBERS = {
    "READ_FILE",
    "SEARCH",
    "LIST_DIR",
    "REPO_MAP",
    "APPLY_PATCH",
    "GIT_DIFF",
    "RUN_COMMAND",
    "RUN_TESTS",
    "PUBLISH_ARTIFACT",
}


class ToolActionObservationContractTest(unittest.TestCase):
    def test_required_tool_names_present(self) -> None:
        names = {m.name for m in ToolContractName}
        self.assertTrue(
            REQUIRED_TOOL_MEMBERS.issubset(names),
            f"missing tools: {REQUIRED_TOOL_MEMBERS - names}",
        )

    def test_tool_contract_status_has_allowed_and_blocked(self) -> None:
        values = {m.value for m in ToolContractStatus}
        self.assertIn("allowed", values)
        self.assertIn("blocked", values)
        self.assertIn("executed", values)
        self.assertIn("failed", values)

    def test_action_record_serializes(self) -> None:
        a = ToolActionRecord(
            action_id="a1",
            session_id="s1",
            job_id="j1",
            tool_name=ToolContractName.READ_FILE,
            arguments={"path": "README.md"},
        )
        d = a.to_dict()
        self.assertEqual(d["action_id"], "a1")
        self.assertEqual(d["tool_name"], "read_file")
        self.assertEqual(d["arguments"], {"path": "README.md"})
        self.assertEqual(d["requested_by"], "phase2_entry")

    def test_allowed_observation_shape(self) -> None:
        obs = ToolObservationRecord(
            action_id="a1",
            session_id="s1",
            job_id="j1",
            tool_name=ToolContractName.READ_FILE,
            status=ToolContractStatus.EXECUTED,
            allowed=True,
            duration_ms=12,
            stdout="content",
            stderr="",
            structured_payload={"bytes_read": 7},
            side_effect_metadata={"path": "README.md"},
            error="",
            return_code=0,
        )
        d = obs.to_dict()
        self.assertTrue(d["allowed"])
        self.assertEqual(d["status"], "executed")
        self.assertEqual(d["tool_name"], "read_file")
        self.assertEqual(d["duration_ms"], 12)
        self.assertEqual(d["structured_payload"], {"bytes_read": 7})
        self.assertEqual(d["side_effect_metadata"], {"path": "README.md"})

    def test_blocked_observation_shape(self) -> None:
        obs = ToolObservationRecord(
            action_id="a1",
            session_id="s1",
            job_id="j1",
            tool_name=ToolContractName.APPLY_PATCH,
            status=ToolContractStatus.BLOCKED,
            allowed=False,
            error="permission_denied",
            return_code=126,
        )
        d = obs.to_dict()
        self.assertFalse(d["allowed"])
        self.assertEqual(d["status"], "blocked")
        self.assertEqual(d["error"], "permission_denied")
        self.assertEqual(d["return_code"], 126)


if __name__ == "__main__":
    unittest.main()
