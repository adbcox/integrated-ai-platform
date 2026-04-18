"""Offline regression for framework.local_command_runner."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.local_command_runner import LocalCommandRunner


class LocalCommandRunnerTest(unittest.TestCase):
    def test_successful_command_returns_normalized_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = LocalCommandRunner(default_timeout_seconds=30)
            t = runner.run(
                ["python3", "-c", "print('ok')"],
                cwd=Path(tmp),
            )
            self.assertEqual(t.return_code, 0)
            self.assertTrue(t.success)
            self.assertIn("ok", t.stdout)
            self.assertGreaterEqual(t.duration_ms, 0)
            self.assertTrue(t.started_at)
            self.assertTrue(t.completed_at)
            self.assertEqual(t.cwd, tmp)

    def test_nonzero_exit_marks_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = LocalCommandRunner(default_timeout_seconds=30)
            t = runner.run(
                ["python3", "-c", "import sys; sys.exit(7)"],
                cwd=Path(tmp),
            )
            self.assertEqual(t.return_code, 7)
            self.assertFalse(t.success)

    def test_missing_binary_returns_127(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = LocalCommandRunner(default_timeout_seconds=30)
            t = runner.run(
                ["this_binary_does_not_exist_xyz"],
                cwd=Path(tmp),
            )
            self.assertEqual(t.return_code, 127)
            self.assertFalse(t.success)
            self.assertIn("not found", t.stderr)

    def test_shell_string_form_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = LocalCommandRunner(default_timeout_seconds=30)
            t = runner.run("echo hello-shell", cwd=Path(tmp))
            self.assertEqual(t.return_code, 0)
            self.assertIn("hello-shell", t.stdout)

    def test_telemetry_to_dict_has_expected_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = LocalCommandRunner(default_timeout_seconds=30)
            t = runner.run(["python3", "-c", "print(1)"], cwd=Path(tmp))
            d = t.to_dict()
            for key in (
                "command",
                "cwd",
                "return_code",
                "stdout",
                "stderr",
                "started_at",
                "completed_at",
                "duration_ms",
                "success",
            ):
                self.assertIn(key, d)


if __name__ == "__main__":
    unittest.main()
