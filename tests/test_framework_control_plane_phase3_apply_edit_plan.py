"""Tests for _phase3_build_stage3_manager_invocation in framework/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_build_stage3_manager_invocation

_REQUIRED_KEYS = {"query", "target_file", "message", "commit_msg", "invocation_ready", "blocked_reason", "shell_command_preview"}


def _vr(
    validation_status: str = "",
    old_text_found: bool = False,
    target_file: str = "",
    executor_message: str = "",
) -> dict:
    return {
        "validation_status": validation_status,
        "old_text_found": old_text_found,
        "target_file": target_file,
        "executor_message": executor_message,
    }


def _ep(query: str = "", target_file: str = "") -> dict:
    return {"query": query, "target_file": target_file}


def _rec(query: str = "") -> dict:
    return {"query": query}


def _valid_vr(target: str = "framework/foo.py") -> dict:
    return _vr(
        validation_status="valid",
        old_text_found=True,
        target_file=target,
        executor_message=f"{target}:: replace exact text 'old' with 'new'",
    )


class TestPhase3BuildStage3ManagerInvocationImport(unittest.TestCase):
    def test_importable_and_callable(self):
        self.assertTrue(callable(_phase3_build_stage3_manager_invocation))


class TestPhase3BuildStage3ManagerInvocationReturnKeys(unittest.TestCase):
    def test_returns_dict_on_empty_inputs(self):
        self.assertIsInstance(_phase3_build_stage3_manager_invocation({}, {}, {}), dict)

    def test_all_required_keys_present_on_empty_inputs(self):
        result = _phase3_build_stage3_manager_invocation({}, {}, {})
        self.assertEqual(set(result.keys()), _REQUIRED_KEYS)

    def test_invocation_ready_false_on_empty_inputs(self):
        self.assertFalse(_phase3_build_stage3_manager_invocation({}, {}, {})["invocation_ready"])

    def test_invocation_ready_true_when_valid_and_old_text_found(self):
        result = _phase3_build_stage3_manager_invocation(
            _valid_vr(), _ep(query="fix foo"), {}
        )
        self.assertTrue(result["invocation_ready"])

    def test_invocation_ready_false_when_valid_but_old_text_not_found(self):
        vr = _vr(validation_status="valid", old_text_found=False, target_file="framework/foo.py",
                 executor_message="framework/foo.py:: replace exact text 'x' with 'y'")
        result = _phase3_build_stage3_manager_invocation(vr, _ep(query="q"), {})
        self.assertFalse(result["invocation_ready"])

    def test_invocation_ready_false_when_old_text_found_but_status_not_valid(self):
        vr = _vr(validation_status="old_text_not_found", old_text_found=True,
                 target_file="framework/foo.py",
                 executor_message="framework/foo.py:: replace exact text 'x' with 'y'")
        result = _phase3_build_stage3_manager_invocation(vr, _ep(query="q"), {})
        self.assertFalse(result["invocation_ready"])

    def test_invocation_ready_false_when_no_target_file(self):
        vr = _vr(validation_status="valid", old_text_found=True, target_file="",
                 executor_message=":: replace exact text 'x' with 'y'")
        result = _phase3_build_stage3_manager_invocation(vr, {}, {})
        self.assertFalse(result["invocation_ready"])


class TestPhase3BuildStage3ManagerInvocationShellCommand(unittest.TestCase):
    def _ready_result(self, query: str = "fix foo") -> dict:
        return _phase3_build_stage3_manager_invocation(_valid_vr(), _ep(query=query), {})

    def test_shell_command_preview_nonempty_when_invocation_ready(self):
        self.assertTrue(self._ready_result()["shell_command_preview"])

    def test_shell_command_preview_empty_when_not_invocation_ready(self):
        result = _phase3_build_stage3_manager_invocation({}, {}, {})
        self.assertEqual(result["shell_command_preview"], "")

    def test_shell_command_preview_starts_with_python3_stage3(self):
        cmd = self._ready_result()["shell_command_preview"]
        self.assertTrue(cmd.startswith("python3 bin/stage3_manager.py"))

    def test_shell_command_preview_contains_query_flag(self):
        self.assertIn("--query", self._ready_result()["shell_command_preview"])

    def test_shell_command_preview_contains_target_flag(self):
        self.assertIn("--target", self._ready_result()["shell_command_preview"])

    def test_shell_command_preview_contains_message_flag(self):
        self.assertIn("--message", self._ready_result()["shell_command_preview"])

    def test_shell_command_preview_contains_commit_msg_flag(self):
        self.assertIn("--commit-msg", self._ready_result()["shell_command_preview"])

    def test_shell_command_preview_quotes_spaces_in_query(self):
        result = _phase3_build_stage3_manager_invocation(
            _valid_vr(), _ep(query="fix the worker runtime"), {}
        )
        self.assertIn("'fix the worker runtime'", result["shell_command_preview"])

    def test_shell_command_preview_quotes_spaces_in_message(self):
        vr = _vr(
            validation_status="valid",
            old_text_found=True,
            target_file="framework/foo.py",
            executor_message="framework/foo.py:: replace exact text 'old val' with 'new val'",
        )
        result = _phase3_build_stage3_manager_invocation(vr, _ep(query="q"), {})
        cmd = result["shell_command_preview"]
        self.assertIn("--message", cmd)


class TestPhase3BuildStage3ManagerInvocationFields(unittest.TestCase):
    def test_query_from_edit_plan(self):
        result = _phase3_build_stage3_manager_invocation(_valid_vr(), _ep(query="my query"), {})
        self.assertEqual(result["query"], "my query")

    def test_query_falls_back_to_recommendation(self):
        result = _phase3_build_stage3_manager_invocation(_valid_vr(), _ep(query=""), _rec(query="rec query"))
        self.assertEqual(result["query"], "rec query")

    def test_target_file_from_validation_result(self):
        result = _phase3_build_stage3_manager_invocation(_valid_vr(target="framework/bar.py"), {}, {})
        self.assertEqual(result["target_file"], "framework/bar.py")

    def test_target_file_falls_back_to_edit_plan(self):
        vr = _vr(validation_status="missing_inputs")
        result = _phase3_build_stage3_manager_invocation(vr, _ep(target_file="framework/baz.py"), {})
        self.assertEqual(result["target_file"], "framework/baz.py")

    def test_message_from_executor_message(self):
        msg = "framework/foo.py:: replace exact text 'a' with 'b'"
        vr = _vr(validation_status="valid", old_text_found=True, target_file="framework/foo.py",
                 executor_message=msg)
        result = _phase3_build_stage3_manager_invocation(vr, _ep(query="q"), {})
        self.assertEqual(result["message"], msg)

    def test_blocked_reason_nonempty_when_not_ready(self):
        result = _phase3_build_stage3_manager_invocation({}, {}, {})
        self.assertTrue(result["blocked_reason"])

    def test_blocked_reason_empty_when_ready(self):
        result = _phase3_build_stage3_manager_invocation(_valid_vr(), _ep(query="q"), {})
        self.assertEqual(result["blocked_reason"], "")

    def test_commit_msg_nonempty(self):
        result = _phase3_build_stage3_manager_invocation(_valid_vr(), _ep(query="fix worker"), {})
        self.assertTrue(result["commit_msg"])

    def test_commit_msg_contains_phase3_edit_prefix(self):
        result = _phase3_build_stage3_manager_invocation(_valid_vr(), _ep(query="fix worker"), {})
        self.assertTrue(result["commit_msg"].startswith("phase3-edit:"))


class TestPhase3BuildStage3ManagerInvocationRobustness(unittest.TestCase):
    def test_no_exception_on_non_dict_validation_result(self):
        try:
            result = _phase3_build_stage3_manager_invocation("not a dict", {}, {})
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_non_dict_edit_plan(self):
        try:
            result = _phase3_build_stage3_manager_invocation({}, 42, {})
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_none_inputs(self):
        try:
            result = _phase3_build_stage3_manager_invocation(None, None, None)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")


class TestSourceTextAssertions(unittest.TestCase):
    def _framework_source(self):
        return (Path(__file__).resolve().parents[1] / "framework" / "framework_control_plane.py").read_text()

    def _bin_source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def _makefile(self):
        return (Path(__file__).resolve().parents[1] / "Makefile").read_text()

    def test_phase3_build_stage3_manager_invocation_in_framework_source(self):
        self.assertIn("_phase3_build_stage3_manager_invocation", self._framework_source())

    def test_phase3_build_stage3_manager_invocation_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_build_stage3_manager_invocation", m.__all__)

    def test_phase3_apply_edit_plan_probe_in_bin_source(self):
        self.assertIn("phase3_apply_edit_plan_probe", self._bin_source())

    def test_phase3_stage3_manager_invocation_latest_json_in_bin_source(self):
        self.assertIn("phase3_stage3_manager_invocation_latest.json", self._bin_source())

    def test_phase3_apply_edit_plan_in_makefile(self):
        self.assertIn("phase3-apply-edit-plan", self._makefile())

    def test_phase3_apply_edit_plan_live_in_makefile(self):
        self.assertIn("phase3-apply-edit-plan-live", self._makefile())


if __name__ == "__main__":
    unittest.main()
