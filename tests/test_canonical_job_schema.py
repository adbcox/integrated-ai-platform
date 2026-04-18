"""Tests for framework.canonical_job_schema."""

from __future__ import annotations

import unittest

from framework.canonical_job_schema import CanonicalJob
from framework.canonical_session_schema import CanonicalSession


class CanonicalJobSchemaTest(unittest.TestCase):
    def test_defaults(self) -> None:
        j = CanonicalJob(job_id="j1", session_id="s1", task_class="quick_fix")
        self.assertEqual(j.status, "planned")
        self.assertEqual(j.final_outcome, "")
        self.assertEqual(j.selected_runtime, "local")
        self.assertEqual(j.constraints, [])
        self.assertEqual(j.allowed_tools, [])
        self.assertEqual(j.stop_conditions, [])

    def test_serializes_to_dict(self) -> None:
        j = CanonicalJob(
            job_id="j1",
            session_id="s1",
            task_class="quick_fix",
            objective="add guard clause",
        )
        d = j.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["job_id"], "j1")
        self.assertEqual(d["session_id"], "s1")
        self.assertEqual(d["task_class"], "quick_fix")
        self.assertEqual(d["status"], "planned")

    def test_from_session_copies_fields(self) -> None:
        s = CanonicalSession(
            session_id="s1",
            task_id="t1",
            task_class="single_file_edit",
            objective="refactor helper",
            constraints=["no network"],
            allowed_tools=["read_file", "apply_patch"],
            risk_tier="elevated",
            stop_conditions=["manual"],
            selected_model_profile="balanced",
            selected_runtime="local",
            workspace_id="ws-1",
            artifact_root="/tmp/art",
            retry_budget=2,
            token_budget=4096,
        )
        j = CanonicalJob.from_session(s, job_id="j1")
        self.assertEqual(j.job_id, "j1")
        self.assertEqual(j.session_id, "s1")
        self.assertEqual(j.task_class, "single_file_edit")
        self.assertEqual(j.objective, "refactor helper")
        self.assertEqual(j.constraints, ["no network"])
        self.assertEqual(j.allowed_tools, ["read_file", "apply_patch"])
        self.assertEqual(j.risk_tier, "elevated")
        self.assertEqual(j.stop_conditions, ["manual"])
        self.assertEqual(j.selected_model_profile, "balanced")
        self.assertEqual(j.workspace_id, "ws-1")
        self.assertEqual(j.artifact_root, "/tmp/art")
        self.assertEqual(j.retry_budget, 2)
        self.assertEqual(j.token_budget, 4096)
        self.assertEqual(j.status, "planned")

    def test_from_session_independent_lists(self) -> None:
        s = CanonicalSession(session_id="s", task_id="t", constraints=["a"])
        j = CanonicalJob.from_session(s, job_id="j")
        j.constraints.append("b")
        self.assertEqual(s.constraints, ["a"])


if __name__ == "__main__":
    unittest.main()
