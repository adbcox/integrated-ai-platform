"""Tests for framework_control_plane Phase 2 manager-wire helpers."""

from __future__ import annotations

import unittest

from framework.framework_control_plane import (
    _phase2_manager_extract,
    _phase2_manager_present,
    _phase2_manager_tool_summary,
)


def _minimal_phase2_payload(*, tool_trace=None) -> dict:
    return {
        "canonical_session": {
            "session_id": "test-session-1",
            "task_id": "test-task-1",
            "selected_runtime": "local",
            "selected_model_profile": "mac_local",
            "final_outcome": "completed",
        },
        "canonical_jobs": [
            {
                "job_id": "test-job-1",
                "session_id": "test-session-1",
                "status": "completed",
                "final_outcome": "completed",
            }
        ],
        "typed_tool_trace": tool_trace if tool_trace is not None else [
            {"tool_name": "search", "status": "executed"},
            {"tool_name": "repo_map", "status": "executed"},
            {"tool_name": "read_file", "status": "blocked"},
        ],
        "permission_decisions": [{"allowed": True}, {"allowed": False}],
        "session_bundle": {"bundle_id": "b1"},
        "final_outcome": "completed",
    }


class TestPhase2ManagerPresent(unittest.TestCase):
    def test_missing_payload_returns_false(self):
        result = _phase2_manager_present({"status": "completed"})
        self.assertFalse(result)

    def test_present_payload_returns_true(self):
        result = _phase2_manager_present(_minimal_phase2_payload())
        self.assertTrue(result)

    def test_partially_missing_returns_false(self):
        payload = _minimal_phase2_payload()
        del payload["canonical_jobs"]
        self.assertFalse(_phase2_manager_present(payload))


class TestPhase2ManagerExtract(unittest.TestCase):
    def test_missing_phase2_payload_present_false(self):
        result = _phase2_manager_extract({"status": "done"})
        self.assertFalse(result["phase2_payload_present"])

    def test_present_phase2_payload_present_true(self):
        result = _phase2_manager_extract(_minimal_phase2_payload())
        self.assertTrue(result["phase2_payload_present"])

    def test_canonical_session_summary_extracts_expected_fields(self):
        result = _phase2_manager_extract(_minimal_phase2_payload())
        summary = result["canonical_session_summary"]
        self.assertEqual(summary["session_id"], "test-session-1")
        self.assertEqual(summary["task_id"], "test-task-1")
        self.assertEqual(summary["selected_runtime"], "local")
        self.assertEqual(summary["selected_model_profile"], "mac_local")
        self.assertEqual(summary["final_outcome"], "completed")

    def test_canonical_job_summaries_at_least_one(self):
        result = _phase2_manager_extract(_minimal_phase2_payload())
        summaries = result["canonical_job_summaries"]
        self.assertIsInstance(summaries, list)
        self.assertGreaterEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["job_id"], "test-job-1")
        self.assertEqual(summaries[0]["session_id"], "test-session-1")

    def test_typed_tool_summary_counts_deterministic(self):
        trace = [
            {"tool_name": "search", "status": "executed"},
            {"tool_name": "repo_map", "status": "executed"},
            {"tool_name": "read_file", "status": "blocked"},
            {"tool_name": "apply_patch", "status": "failed"},
        ]
        result = _phase2_manager_extract(_minimal_phase2_payload(tool_trace=trace))
        summary = result["typed_tool_summary"]
        self.assertEqual(summary["executed_count"], 2)
        self.assertEqual(summary["blocked_count"], 1)
        self.assertEqual(summary["failed_count"], 1)
        self.assertEqual(summary["tool_count"], 4)

    def test_tool_names_sorted_and_stable(self):
        trace = [
            {"tool_name": "repo_map", "status": "executed"},
            {"tool_name": "apply_patch", "status": "executed"},
            {"tool_name": "search", "status": "executed"},
        ]
        result = _phase2_manager_extract(_minimal_phase2_payload(tool_trace=trace))
        names = result["typed_tool_summary"]["tool_names_sorted"]
        self.assertEqual(names, sorted(names))
        self.assertEqual(names, ["apply_patch", "repo_map", "search"])


class TestPhase2ManagerToolSummary(unittest.TestCase):
    def test_malformed_entries_ignored(self):
        payload = {"typed_tool_trace": [None, 42, {"tool_name": "search", "status": "executed"}]}
        summary = _phase2_manager_tool_summary(payload)
        self.assertEqual(summary["tool_count"], 1)
        self.assertEqual(summary["executed_count"], 1)

    def test_empty_trace_returns_zeros(self):
        summary = _phase2_manager_tool_summary({"typed_tool_trace": []})
        self.assertEqual(summary["tool_count"], 0)
        self.assertEqual(summary["blocked_count"], 0)


if __name__ == "__main__":
    unittest.main()
