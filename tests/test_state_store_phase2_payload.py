"""Tests for Phase 2 payload persistence in StateStore."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from framework.state_store import StateStore


class StateStorePhase2PayloadTest(unittest.TestCase):
    def test_phase2_keys_persisted_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td))
            payload = {
                "job_id": "j1",
                "status": "completed",
                "canonical_session": {"session_id": "s1", "task_id": "j1"},
                "canonical_jobs": [{"job_id": "j1", "session_id": "s1"}],
                "typed_tool_trace": [{"kind": "tool_action", "tool_name": "run_command"}],
                "permission_decisions": [{"allowed": True}],
                "session_bundle": {"session": {}, "jobs": [], "tool_trace": []},
                "final_outcome": "completed",
            }
            path = store.save_result("j1", payload)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["canonical_session"], payload["canonical_session"])
            self.assertEqual(persisted["canonical_jobs"], payload["canonical_jobs"])
            self.assertEqual(persisted["typed_tool_trace"], payload["typed_tool_trace"])
            self.assertEqual(persisted["permission_decisions"], payload["permission_decisions"])
            self.assertEqual(persisted["session_bundle"], payload["session_bundle"])
            self.assertEqual(persisted["final_outcome"], "completed")

    def test_phase2_payload_present_true_when_keys_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td))
            payload = {
                "job_id": "j1",
                "status": "completed",
                "canonical_session": {"session_id": "s1"},
                "canonical_jobs": [{"job_id": "j1"}],
                "typed_tool_trace": [],
            }
            path = store.save_result("j1", payload)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertIs(persisted.get("phase2_payload_present"), True)

    def test_phase2_payload_present_false_when_keys_absent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td))
            payload = {"job_id": "j1", "status": "completed"}
            path = store.save_result("j1", payload)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertIs(persisted.get("phase2_payload_present"), False)

    def test_existing_payload_keys_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td))
            payload = {
                "job_id": "j1",
                "status": "completed",
                "output": "hello",
                "validation": {"passed": True},
                "failure_class": "",
            }
            path = store.save_result("j1", payload)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["output"], "hello")
            self.assertEqual(persisted["validation"], {"passed": True})
            self.assertEqual(persisted["failure_class"], "")
            self.assertEqual(persisted.get("outcome_class"), "unknown")
            self.assertIs(persisted.get("phase2_payload_present"), False)


if __name__ == "__main__":
    unittest.main()
