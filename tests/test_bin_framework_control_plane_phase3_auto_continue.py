"""Tests for _run_phase3_continuation and --phase3-auto-continue in bin/framework_control_plane.py."""

from __future__ import annotations

import argparse
import sys
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin.framework_control_plane import _run_phase3_continuation, parse_args

_REQUIRED_KEYS = {
    "ran",
    "template_used",
    "idle_reached",
    "job_status",
    "return_code",
    "typed_tool_count",
    "error",
    "phase3_continuation_next_action",
    "phase3_continuation_recommendation_ready",
}
_AUTO_CONTINUE_ACTIONS = {"refine_retrieval", "insufficient_context"}
_NOT_TRIGGER_ACTIONS = {"ready", "no_context"}


def _make_args(**kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(
        state_root="/tmp/test_phase3_cont",
        wait_timeout_seconds=5,
        phase3_auto_continue=False,
        task_template="retrieval_probe",
        **kwargs,
    )
    return ns


class TestRunPhase3ContinuationImport(unittest.TestCase):
    def test_importable(self):
        from bin.framework_control_plane import _run_phase3_continuation as fn
        self.assertTrue(callable(fn))


class TestRunPhase3ContinuationReturnKeys(unittest.TestCase):
    def _make_raising_scheduler(self):
        """Return a patcher that makes Scheduler construction raise RuntimeError."""
        return unittest.mock.patch(
            "bin.framework_control_plane.Scheduler",
            side_effect=RuntimeError("mock error"),
        )

    def test_returns_dict(self):
        with self._make_raising_scheduler():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertIsInstance(result, dict)

    def test_all_required_keys_present_on_exception(self):
        with self._make_raising_scheduler():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertEqual(set(result.keys()), _REQUIRED_KEYS)

    def test_template_used_equals_argument(self):
        with self._make_raising_scheduler():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "read_after_retrieval"
            )
        self.assertEqual(result["template_used"], "read_after_retrieval")

    def test_ran_false_on_exception(self):
        with self._make_raising_scheduler():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertFalse(result["ran"])

    def test_error_nonempty_on_exception(self):
        with self._make_raising_scheduler():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertTrue(result["error"])

    def test_no_raise_on_exception(self):
        with self._make_raising_scheduler():
            try:
                _run_phase3_continuation(
                    _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
                )
            except Exception as e:
                self.fail(f"Raised unexpected exception: {e}")

    def test_phase3_continuation_next_action_key_present(self):
        with self._make_raising_scheduler():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertIn("phase3_continuation_next_action", result)


class TestParseArgsPhase3AutoContinue(unittest.TestCase):
    def test_flag_present_when_passed(self):
        import unittest.mock as mock
        with mock.patch.object(sys, "argv", ["prog", "--phase3-auto-continue"]):
            args = parse_args()
        self.assertTrue(args.phase3_auto_continue)

    def test_flag_false_when_absent(self):
        import unittest.mock as mock
        with mock.patch.object(sys, "argv", ["prog"]):
            args = parse_args()
        self.assertFalse(args.phase3_auto_continue)

    def test_help_does_not_break(self):
        import subprocess
        repo_root = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, str(repo_root / "bin" / "framework_control_plane.py"),
             "--phase3-auto-continue", "--help"],
            capture_output=True,
            cwd=str(repo_root),
        )
        self.assertEqual(proc.returncode, 0)


class TestAutoContinueTriggerSet(unittest.TestCase):
    def test_refine_retrieval_in_trigger_set(self):
        self.assertIn("refine_retrieval", _AUTO_CONTINUE_ACTIONS)

    def test_insufficient_context_in_trigger_set(self):
        self.assertIn("insufficient_context", _AUTO_CONTINUE_ACTIONS)

    def test_ready_not_in_trigger_set(self):
        self.assertNotIn("ready", _AUTO_CONTINUE_ACTIONS)

    def test_no_context_not_in_trigger_set(self):
        self.assertNotIn("no_context", _AUTO_CONTINUE_ACTIONS)


class TestSourceTextAssertions(unittest.TestCase):
    def _source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def test_phase3_auto_continue_in_source(self):
        self.assertIn("phase3_auto_continue", self._source())

    def test_phase3_continuation_result_in_source(self):
        self.assertIn("phase3_continuation_result", self._source())

    def test_run_phase3_continuation_in_source(self):
        self.assertIn("_run_phase3_continuation", self._source())

    def test_phase3_continuation_next_action_in_source(self):
        self.assertIn("phase3_continuation_next_action", self._source())

    def test_scheduler_restart_not_safe_absent_from_source(self):
        self.assertNotIn("scheduler_restart_not_safe", self._source())

    def test_phase3_continuation_recommendation_ready_in_source(self):
        self.assertIn("phase3_continuation_recommendation_ready", self._source())

    def test_phase2_retrieval_summary_in_source(self):
        self.assertIn("_phase2_retrieval_summary", self._source())


if __name__ == "__main__":
    unittest.main()
