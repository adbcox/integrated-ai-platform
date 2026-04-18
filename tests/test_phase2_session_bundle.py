"""Tests for framework.phase2_session_bundle."""

from __future__ import annotations

import unittest

from framework.canonical_job_schema import CanonicalJob
from framework.canonical_session_schema import CanonicalSession
from framework.phase2_session_bundle import build_phase2_session_bundle
from framework.tool_action_observation_contract import (
    ToolContractName,
    ToolContractStatus,
)
from framework.tool_contract_builders import (
    build_blocked_tool_observation,
    build_tool_action,
    build_tool_observation,
)


REQUIRED_BUNDLE_KEYS = {
    "session",
    "jobs",
    "tool_trace",
    "permission_decisions",
    "final_outcome",
}


class Phase2SessionBundleTest(unittest.TestCase):
    def test_bundle_contains_required_keys(self) -> None:
        s = CanonicalSession(session_id="s", task_id="t")
        bundle = build_phase2_session_bundle(session=s)
        self.assertTrue(REQUIRED_BUNDLE_KEYS.issubset(set(bundle.keys())))
        self.assertEqual(bundle["session"]["session_id"], "s")
        self.assertEqual(bundle["jobs"], [])
        self.assertEqual(bundle["tool_trace"], [])
        self.assertEqual(bundle["permission_decisions"], [])

    def test_bundle_includes_jobs_and_tool_trace(self) -> None:
        s = CanonicalSession(session_id="s", task_id="t", task_class="quick_fix")
        j = CanonicalJob.from_session(s, job_id="j")
        a = build_tool_action(
            action_id="a1",
            session_id="s",
            job_id="j",
            tool_name=ToolContractName.READ_FILE,
            arguments={"path": "README.md"},
        )
        ok = build_tool_observation(
            action=a,
            status=ToolContractStatus.EXECUTED,
            allowed=True,
            stdout="content",
        )
        blocked = build_blocked_tool_observation(action=a, reason="denied")
        bundle = build_phase2_session_bundle(
            session=s,
            jobs=[j],
            tool_actions=[a],
            tool_observations=[ok, blocked],
            permission_decisions=[{"allowed": True}, {"allowed": False}],
            final_outcome="completed",
        )
        self.assertEqual(len(bundle["jobs"]), 1)
        self.assertEqual(bundle["jobs"][0]["job_id"], "j")
        kinds = [entry["kind"] for entry in bundle["tool_trace"]]
        self.assertIn("tool_action", kinds)
        self.assertIn("tool_observation", kinds)
        self.assertEqual(bundle["final_outcome"], "completed")
        self.assertEqual(len(bundle["permission_decisions"]), 2)

    def test_bundle_falls_back_to_session_final_outcome(self) -> None:
        s = CanonicalSession(session_id="s", task_id="t", final_outcome="failed")
        bundle = build_phase2_session_bundle(session=s)
        self.assertEqual(bundle["final_outcome"], "failed")


if __name__ == "__main__":
    unittest.main()
