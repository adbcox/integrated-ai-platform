"""Offline tests for framework/local_command_runner.py.

Uses monkeypatched KNOWN_FRAMEWORK_COMMANDS aliases to safe shell builtins so
no real make targets are invoked.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _patched_commands():
    """Return a safe command map for offline test use."""
    return {
        "check": "echo test_output",
        "quick": "true",
        "test_offline": "false",
    }


class KnownCommandsTest(unittest.TestCase):
    def test_check_alias_exists(self):
        from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS
        self.assertIn("check", KNOWN_FRAMEWORK_COMMANDS)

    def test_quick_alias_exists(self):
        from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS
        self.assertIn("quick", KNOWN_FRAMEWORK_COMMANDS)

    def test_test_offline_alias_exists(self):
        from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS
        self.assertIn("test_offline", KNOWN_FRAMEWORK_COMMANDS)

    def test_all_command_values_are_nonempty_strings(self):
        from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS
        for name, value in KNOWN_FRAMEWORK_COMMANDS.items():
            self.assertIsInstance(value, str, msg=f"{name} value is not a string")
            self.assertTrue(value.strip(), msg=f"{name} value is empty")

    def test_unknown_command_raises_value_error(self):
        from framework.local_command_runner import LocalCommandRunner
        runner = LocalCommandRunner()
        with self.assertRaises(ValueError):
            runner.run("this_command_does_not_exist")


class LocalCommandResultTest(unittest.TestCase):
    def _run_patched(self, command_name: str, cwd=None):
        import framework.local_command_runner as m
        with mock.patch.object(m, "KNOWN_FRAMEWORK_COMMANDS", _patched_commands()):
            from framework.local_command_runner import LocalCommandRunner
            runner = LocalCommandRunner(cwd=cwd)
            return runner.run(command_name)

    def test_successful_run_returns_all_required_fields(self):
        result = self._run_patched("check")
        self.assertTrue(result.command_name)
        self.assertTrue(result.argv)
        self.assertTrue(result.cwd)
        self.assertIsInstance(result.return_code, int)
        self.assertIsInstance(result.stdout, str)
        self.assertIsInstance(result.stderr, str)
        self.assertTrue(result.started_at)
        self.assertTrue(result.completed_at)
        self.assertGreaterEqual(result.duration_ms, 0)
        self.assertIsInstance(result.success, bool)

    def test_zero_exit_code_sets_success_true(self):
        result = self._run_patched("quick")  # "true" exits 0
        self.assertEqual(result.return_code, 0)
        self.assertTrue(result.success)

    def test_nonzero_exit_code_sets_success_false(self):
        result = self._run_patched("test_offline")  # "false" exits 1
        self.assertNotEqual(result.return_code, 0)
        self.assertFalse(result.success)

    def test_stdout_captured(self):
        result = self._run_patched("check")  # "echo test_output"
        self.assertIn("test_output", result.stdout)

    def test_duration_ms_is_non_negative(self):
        result = self._run_patched("quick")
        self.assertGreaterEqual(result.duration_ms, 0)

    def test_to_dict_has_expected_keys(self):
        result = self._run_patched("quick")
        d = result.to_dict()
        for key in (
            "command_name",
            "argv",
            "cwd",
            "return_code",
            "stdout",
            "stderr",
            "started_at",
            "completed_at",
            "duration_ms",
            "success",
        ):
            self.assertIn(key, d, msg=f"missing key {key!r} in to_dict()")


class TelemetryConversionTest(unittest.TestCase):
    def _run_patched(self, command_name: str):
        import framework.local_command_runner as m
        with mock.patch.object(m, "KNOWN_FRAMEWORK_COMMANDS", _patched_commands()):
            from framework.local_command_runner import LocalCommandRunner
            runner = LocalCommandRunner()
            return runner.run(command_name)

    def test_to_telemetry_returns_command_telemetry(self):
        from framework.runtime_telemetry_schema import CommandTelemetry
        result = self._run_patched("quick")
        telemetry = result.to_telemetry()
        self.assertIsInstance(telemetry, CommandTelemetry)

    def test_telemetry_command_matches_argv(self):
        result = self._run_patched("quick")
        telemetry = result.to_telemetry()
        self.assertEqual(telemetry.command, result.argv)

    def test_telemetry_cwd_matches_result_cwd(self):
        result = self._run_patched("quick")
        telemetry = result.to_telemetry()
        self.assertEqual(telemetry.cwd, result.cwd)

    def test_telemetry_success_matches_result_success(self):
        result = self._run_patched("quick")
        telemetry = result.to_telemetry()
        self.assertEqual(telemetry.success, result.success)

    def test_telemetry_failure_matches_result_failure(self):
        result = self._run_patched("test_offline")  # "false"
        telemetry = result.to_telemetry()
        self.assertEqual(telemetry.success, result.success)
        self.assertFalse(telemetry.success)


if __name__ == "__main__":
    unittest.main()
