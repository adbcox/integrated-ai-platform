"""Tests for _run_repo_quick_check in bin/stage3_manager.py."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.stage3_manager import _run_repo_quick_check  # noqa: E402


class RepoQuickCheckTest(unittest.TestCase):
    def test_passing_quick_returns_passed(self) -> None:
        ok, note = _run_repo_quick_check("bin/stage3_manager.py")
        self.assertTrue(ok, f"expected pass, got note={note!r}")
        self.assertEqual(note, "repo_quick_passed")

    def test_failing_quick_returns_failed(self) -> None:
        fake = MagicMock()
        fake.returncode = 1
        fake.stderr = "FAIL: some check"
        fake.stdout = ""
        with patch("subprocess.run", return_value=fake):
            ok, note = _run_repo_quick_check("framework/worker_runtime.py")
        self.assertFalse(ok)
        self.assertTrue(note.startswith("repo_quick_failed:"), note)

    def test_timeout_returns_repo_quick_timeout(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("make", 30)):
            ok, note = _run_repo_quick_check("bin/stage3_manager.py")
        self.assertFalse(ok)
        self.assertEqual(note, "repo_quick_timeout")

    def test_exception_returns_repo_quick_exception(self) -> None:
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            ok, note = _run_repo_quick_check("bin/stage3_manager.py")
        self.assertFalse(ok)
        self.assertTrue(note.startswith("repo_quick_exception:"), note)

    def test_changed_files_env_set_to_target(self) -> None:
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["env"] = kwargs.get("env", {})
            m = MagicMock()
            m.returncode = 0
            return m

        with patch("subprocess.run", side_effect=fake_run):
            _run_repo_quick_check("bin/stage3_manager.py")
        self.assertEqual(captured["env"].get("CHANGED_FILES"), "bin/stage3_manager.py")

    def test_custom_repo_root_passed_as_cwd(self) -> None:
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cwd"] = kwargs.get("cwd")
            m = MagicMock()
            m.returncode = 0
            return m

        with patch("subprocess.run", side_effect=fake_run):
            _run_repo_quick_check("bin/stage3_manager.py", repo_root=REPO_ROOT)
        self.assertEqual(captured.get("cwd"), str(REPO_ROOT))

    def test_return_type_is_bool_str(self) -> None:
        ok, note = _run_repo_quick_check("bin/stage3_manager.py")
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)

    def test_empty_target_does_not_raise(self) -> None:
        result = _run_repo_quick_check("")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class RepoQuickCheckSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")

    def test_function_exists_in_source(self) -> None:
        self.assertIn("_run_repo_quick_check", self._source)

    def test_repo_quick_check_status_in_source(self) -> None:
        self.assertIn("repo_quick_check_status", self._source)

    def test_repo_quick_check_note_in_source(self) -> None:
        self.assertIn("repo_quick_check_note", self._source)

    def test_reverted_repo_quick_failure_in_source(self) -> None:
        self.assertIn("reverted_repo_quick_failure", self._source)

    def test_repo_quick_passed_in_source(self) -> None:
        self.assertIn("repo_quick_passed", self._source)

    def test_skipped_prior_gate_failed_in_source(self) -> None:
        self.assertIn("skipped_prior_gate_failed", self._source)

    def test_changed_files_in_source(self) -> None:
        self.assertIn("CHANGED_FILES", self._source)


if __name__ == "__main__":
    unittest.main()
