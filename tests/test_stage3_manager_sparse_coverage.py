"""Tests for _run_smoke_tests in bin/stage3_manager.py (all mock-based)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.stage3_manager import _run_smoke_tests  # noqa: E402


class RunSmokeTestsTest(unittest.TestCase):
    def test_passing_subprocess_returns_smoke_passed(self) -> None:
        fake = MagicMock()
        fake.returncode = 0
        fake.stdout = "10 passed in 0.3s\n"
        fake.stderr = ""
        with patch("subprocess.run", return_value=fake):
            ok, note = _run_smoke_tests()
        self.assertTrue(ok)
        self.assertTrue(note.startswith("smoke_passed:"), note)

    def test_failing_subprocess_returns_smoke_failed(self) -> None:
        fake = MagicMock()
        fake.returncode = 1
        fake.stdout = "1 failed in 0.2s\n"
        fake.stderr = ""
        with patch("subprocess.run", return_value=fake):
            ok, note = _run_smoke_tests()
        self.assertFalse(ok)
        self.assertTrue(note.startswith("smoke_failed:"), note)

    def test_timeout_returns_smoke_timeout_20s(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 20)):
            ok, note = _run_smoke_tests()
        self.assertFalse(ok)
        self.assertEqual(note, "smoke_timeout:20s")

    def test_exception_returns_smoke_exception(self) -> None:
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            ok, note = _run_smoke_tests()
        self.assertFalse(ok)
        self.assertTrue(note.startswith("smoke_exception:"), note)

    def test_nonexistent_tests_dir_returns_smoke_no_dir(self) -> None:
        ok, note = _run_smoke_tests(repo_root=Path("/nonexistent/xyzzy_smoke_test_root"))
        self.assertTrue(ok)
        self.assertEqual(note, "smoke_no_dir")

    def test_empty_tests_dir_returns_smoke_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            ok, note = _run_smoke_tests(repo_root=root)
        self.assertTrue(ok)
        self.assertEqual(note, "smoke_no_files")

    def test_return_type_is_bool_str(self) -> None:
        fake = MagicMock()
        fake.returncode = 0
        fake.stdout = "ok\n"
        fake.stderr = ""
        with patch("subprocess.run", return_value=fake):
            ok, note = _run_smoke_tests()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)

    def test_explicit_corpus_file_passed_in_cmd(self) -> None:
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = list(cmd)
            m = MagicMock()
            m.returncode = 0
            m.stdout = "1 passed\n"
            m.stderr = ""
            return m

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            corpus_file = tests / "test_stage3_manager_post_apply_validation.py"
            corpus_file.write_text("def test_dummy(): pass\n")
            with patch("subprocess.run", side_effect=fake_run):
                ok, note = _run_smoke_tests(repo_root=root)
        self.assertTrue(ok)
        self.assertIn(str(corpus_file), captured.get("cmd", []))


class SmokeSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")

    def test_run_smoke_tests_in_source(self) -> None:
        self.assertIn("_run_smoke_tests", self._source)

    def test_smoke_passed_in_source(self) -> None:
        self.assertIn("smoke_passed", self._source)

    def test_smoke_failed_in_source(self) -> None:
        self.assertIn("smoke_failed", self._source)

    def test_smoke_timeout_in_source(self) -> None:
        self.assertIn("smoke_timeout", self._source)

    def test_smoke_no_files_in_source(self) -> None:
        self.assertIn("smoke_no_files", self._source)

    def test_reverted_smoke_failure_in_source(self) -> None:
        self.assertIn("reverted_smoke_failure", self._source)

    def test_if_discovered_branch_in_source(self) -> None:
        self.assertIn("if discovered:", self._source)


if __name__ == "__main__":
    unittest.main()
