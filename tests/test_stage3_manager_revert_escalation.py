"""Source assertions for revert-failure escalation in bin/stage3_manager.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))


class RevertEscalationSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")

    def test_revert_failure_dirty_state_in_source(self) -> None:
        self.assertIn("revert_failure_dirty_state", self._src)

    def test_dirty_final_status_in_source(self) -> None:
        self.assertIn('"dirty"', self._src)

    def test_fatal_message_in_source(self) -> None:
        self.assertIn("FATAL", self._src)

    def test_dirty_message_in_source(self) -> None:
        self.assertIn("repo state is dirty", self._src)

    def test_manual_intervention_in_source(self) -> None:
        self.assertIn("Manual intervention required", self._src)

    def test_all_four_gates_have_escalation(self) -> None:
        self.assertGreaterEqual(self._src.count("revert_failure_dirty_state"), 5)

    def test_fatal_exit_after_trace_write_in_source(self) -> None:
        trace_pos = self._src.rfind("append_trace(entry)")
        fatal_pos = self._src.find("revert_failure_dirty_state", trace_pos)
        self.assertGreater(fatal_pos, trace_pos)

    def test_accepted_false_set_in_all_else_branches(self) -> None:
        self.assertGreaterEqual(self._src.count('classification = "revert_failure_dirty_state"'), 4)

    def test_commit_hash_none_set_in_else_branches(self) -> None:
        self.assertGreaterEqual(self._src.count("commit_hash = None"), 8)


if __name__ == "__main__":
    unittest.main()
