"""Tests for Phase 2 canonical session/job + typed tool wiring in WorkerRuntime."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.runtime_validation_pack import (
    REQUIRED_PHASE2_RUNTIME_KEYS,
    run_phase2_runtime_wire_validation,
)


class WorkerRuntimePhase2IntegrationTest(unittest.TestCase):
    def test_canonical_session_has_requested_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=True, tmp_root=Path(td)
            )
        session = r.get("canonical_session")
        self.assertIsInstance(session, dict)
        assert isinstance(session, dict)
        self.assertEqual(session.get("session_id"), "phase2-wire-session-allow")
        self.assertEqual(session.get("task_class"), "validation_check_execution")

    def test_at_least_one_canonical_job(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=True, tmp_root=Path(td)
            )
        jobs = r.get("canonical_jobs")
        self.assertIsInstance(jobs, list)
        assert isinstance(jobs, list)
        self.assertGreaterEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["session_id"], "phase2-wire-session-allow")

    def test_typed_tool_trace_contains_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=True, tmp_root=Path(td)
            )
        trace = r.get("typed_tool_trace")
        self.assertIsInstance(trace, list)
        assert isinstance(trace, list)
        kinds = {entry.get("kind") for entry in trace if isinstance(entry, dict)}
        self.assertIn("tool_action", kinds)
        self.assertIn("tool_observation", kinds)
        for entry in trace:
            self.assertIn("action_id", entry)
            self.assertIn("session_id", entry)
            self.assertIn("job_id", entry)
            self.assertIn("tool_name", entry)

    def test_blocked_path_emits_blocked_typed_observation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=False, tmp_root=Path(td)
            )
        trace = r.get("typed_tool_trace") or []
        blocked = [
            e
            for e in trace
            if isinstance(e, dict)
            and e.get("kind") == "tool_observation"
            and e.get("tool_name") == "run_command"
            and e.get("status") == "blocked"
            and e.get("allowed") is False
        ]
        self.assertTrue(blocked, f"expected blocked run_command observation; got: {trace!r}")

    def test_final_outcome_and_required_keys_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=True, tmp_root=Path(td)
            )
        self.assertTrue(REQUIRED_PHASE2_RUNTIME_KEYS.issubset(set(r.keys())))
        self.assertEqual(r.get("final_outcome"), "completed")


if __name__ == "__main__":
    unittest.main()
