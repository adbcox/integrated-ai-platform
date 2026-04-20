"""Tests for _run_repo_fast_check in bin/stage3_manager.py."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.stage3_manager import _run_repo_fast_check  # noqa: E402


class RepoFastCheckTest(unittest.TestCase):
    def test_passing_make_check_returns_passed(self) -> None:
        ok, note = _run_repo_fast_check()
        self.assertTrue(ok, f"expected pass, got note={note!r}")
        self.assertEqual(note, "repo_check_passed")

    def test_failing_make_check_returns_failed(self) -> None:
        fake = MagicMock()
        fake.returncode = 1
        fake.stderr = "syntax error in something"
        fake.stdout = ""
        with patch("subprocess.run", return_value=fake):
            ok, note = _run_repo_fast_check()
        self.assertFalse(ok)
        self.assertTrue(note.startswith("repo_check_failed:"), note)

    def test_timeout_returns_repo_check_timeout(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("make", 60)):
            ok, note = _run_repo_fast_check()
        self.assertFalse(ok)
        self.assertEqual(note, "repo_check_timeout")

    def test_exception_returns_repo_check_exception(self) -> None:
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            ok, note = _run_repo_fast_check()
        self.assertFalse(ok)
        self.assertTrue(note.startswith("repo_check_exception:"), note)

    def test_custom_repo_root_accepted(self) -> None:
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cwd"] = kwargs.get("cwd")
            m = MagicMock()
            m.returncode = 0
            return m

        custom = REPO_ROOT
        with patch("subprocess.run", side_effect=fake_run):
            _run_repo_fast_check(repo_root=custom)
        self.assertEqual(captured.get("cwd"), str(custom))

    def test_return_type_is_bool_str(self) -> None:
        ok, note = _run_repo_fast_check()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)

    def test_source_contains_skipped_prior_gate_failed(self) -> None:
        source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")
        self.assertIn("skipped_prior_gate_failed", source)


class RepoFastCheckSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")

    def test_function_exists_in_source(self) -> None:
        self.assertIn("_run_repo_fast_check", self._source)

    def test_repo_fast_check_status_in_source(self) -> None:
        self.assertIn("repo_fast_check_status", self._source)

    def test_repo_fast_check_note_in_source(self) -> None:
        self.assertIn("repo_fast_check_note", self._source)

    def test_reverted_repo_check_failure_in_source(self) -> None:
        self.assertIn("reverted_repo_check_failure", self._source)

    def test_repo_check_passed_in_source(self) -> None:
        self.assertIn("repo_check_passed", self._source)


if __name__ == "__main__":
    unittest.main()
