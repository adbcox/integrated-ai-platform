"""Tests for framework.canonical_session_schema."""

from __future__ import annotations

import unittest

from framework.canonical_session_schema import CanonicalSession


class CanonicalSessionSchemaTest(unittest.TestCase):
    def test_required_fields_and_defaults(self) -> None:
        s = CanonicalSession(session_id="s1", task_id="t1")
        self.assertEqual(s.session_id, "s1")
        self.assertEqual(s.task_id, "t1")
        self.assertEqual(s.selected_runtime, "local")
        self.assertEqual(s.risk_tier, "standard")
        self.assertEqual(s.network_policy, "disabled")
        self.assertEqual(s.constraints, [])
        self.assertEqual(s.allowed_tools, [])
        self.assertEqual(s.tool_trace, [])
        self.assertEqual(s.permission_decisions, [])
        self.assertEqual(s.patch_sets, [])
        self.assertEqual(s.command_results, [])
        self.assertEqual(s.test_results, [])
        self.assertEqual(s.escalation_history, [])
        self.assertEqual(s.benchmark_linkage, {})
        self.assertEqual(s.promotion_linkage, {})

    def test_serializes_to_dict(self) -> None:
        s = CanonicalSession(
            session_id="s1",
            task_id="t1",
            objective="close phase 2 entry",
            constraints=["no network"],
            allowed_tools=["read_file", "search"],
            selected_model_profile="fast",
        )
        d = s.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["session_id"], "s1")
        self.assertEqual(d["objective"], "close phase 2 entry")
        self.assertEqual(d["allowed_tools"], ["read_file", "search"])
        self.assertEqual(d["selected_model_profile"], "fast")

    def test_independent_default_lists(self) -> None:
        a = CanonicalSession(session_id="a", task_id="a")
        b = CanonicalSession(session_id="b", task_id="b")
        a.constraints.append("x")
        self.assertEqual(b.constraints, [])

    def test_mutable_trace_fields_accept_dicts(self) -> None:
        s = CanonicalSession(session_id="s", task_id="t")
        s.tool_trace.append({"kind": "tool_action", "tool_name": "read_file"})
        s.permission_decisions.append({"allowed": True})
        d = s.to_dict()
        self.assertEqual(len(d["tool_trace"]), 1)
        self.assertEqual(len(d["permission_decisions"]), 1)


if __name__ == "__main__":
    unittest.main()
