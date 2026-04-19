"""Tests for _phase3_validate_edit_plan in framework/framework_control_plane.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_validate_edit_plan

_REQUIRED_KEYS = {
    "old_text",
    "new_text",
    "target_file",
    "old_text_found",
    "validation_status",
    "preview_snippet",
    "executor_message",
}

_PLAN_TEXT_WITH_FORMAT = "framework/code_executor.py:: replace exact text 'old_value' with 'new_value'"
_PLAN_TEXT_NO_FORMAT = "Just some prose with no replacement instruction."


def _make_edit_plan(plan_text: str = _PLAN_TEXT_WITH_FORMAT, target_file: str = "framework/code_executor.py") -> dict:
    return {"plan_text": plan_text, "target_file": target_file, "plan_ready": True}


class TestPhase3ValidateEditPlanImport(unittest.TestCase):
    def test_importable(self):
        from framework.framework_control_plane import _phase3_validate_edit_plan as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_validate_edit_plan", m.__all__)


class TestPhase3ValidateEditPlanReturnKeys(unittest.TestCase):
    def test_returns_dict_on_empty_inputs(self):
        result = _phase3_validate_edit_plan({}, "/tmp")
        self.assertIsInstance(result, dict)

    def test_all_required_keys_present_on_empty_inputs(self):
        result = _phase3_validate_edit_plan({}, "/tmp")
        self.assertEqual(set(result.keys()), _REQUIRED_KEYS)

    def test_missing_inputs_status_on_empty_dict(self):
        result = _phase3_validate_edit_plan({}, "/tmp")
        self.assertEqual(result["validation_status"], "missing_inputs")

    def test_no_replacement_format_status(self):
        result = _phase3_validate_edit_plan(_make_edit_plan(plan_text=_PLAN_TEXT_NO_FORMAT), "/tmp")
        self.assertEqual(result["validation_status"], "no_replacement_format")

    def test_target_file_missing_status(self):
        result = _phase3_validate_edit_plan(_make_edit_plan(), "/nonexistent_repo_root_xyz")
        self.assertEqual(result["validation_status"], "target_file_missing")

    def test_old_text_found_true_when_present(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("# header\nold_value = 1\n# footer\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertTrue(result["old_text_found"])

    def test_old_text_found_false_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("# no old text here\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertFalse(result["old_text_found"])

    def test_validation_status_valid_when_found(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("old_value = 1\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertEqual(result["validation_status"], "valid")

    def test_validation_status_old_text_not_found_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("something_else = 1\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertEqual(result["validation_status"], "old_text_not_found")

    def test_executor_message_nonempty_when_valid(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("old_value = 1\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertTrue(result["executor_message"])
        self.assertIn("replace exact text", result["executor_message"])

    def test_executor_message_empty_when_not_found(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("something_else = 1\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertEqual(result["executor_message"], "")

    def test_preview_snippet_nonempty_and_contains_old_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("prefix_text old_value suffix_text\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertTrue(result["preview_snippet"])
        self.assertIn("old_value", result["preview_snippet"])

    def test_preview_snippet_empty_when_not_found(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("something_else = 1\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertEqual(result["preview_snippet"], "")

    def test_no_exception_on_non_dict_edit_plan(self):
        try:
            _phase3_validate_edit_plan("not a dict", "/tmp")  # type: ignore[arg-type]
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_none_inputs(self):
        try:
            _phase3_validate_edit_plan(None, None)  # type: ignore[arg-type]
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_empty_repo_root(self):
        plan = {"plan_text": "myfile.py:: replace exact text 'old' with 'new'", "target_file": "myfile.py"}
        try:
            _phase3_validate_edit_plan(plan, "")
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_all_required_keys_present_when_valid(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "myfile.py"
            target.write_text("old_value = 1\n", encoding="utf-8")
            plan = {"plan_text": "myfile.py:: replace exact text 'old_value' with 'new_value'", "target_file": "myfile.py"}
            result = _phase3_validate_edit_plan(plan, tmp_dir)
        self.assertEqual(set(result.keys()), _REQUIRED_KEYS)


class TestSourceTextAssertions(unittest.TestCase):
    def _fw_source(self):
        return (Path(__file__).resolve().parents[1] / "framework" / "framework_control_plane.py").read_text()

    def _bin_source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def _makefile_source(self):
        return (Path(__file__).resolve().parents[1] / "Makefile").read_text()

    def test_phase3_validate_edit_plan_in_framework_source(self):
        self.assertIn("_phase3_validate_edit_plan", self._fw_source())

    def test_executor_message_in_framework_source(self):
        self.assertIn("executor_message", self._fw_source())

    def test_phase3_validate_edit_plan_probe_in_bin_source(self):
        self.assertIn("phase3_validate_edit_plan_probe", self._bin_source())

    def test_phase3_validate_edit_plan_in_makefile(self):
        self.assertIn("phase3-validate-edit-plan", self._makefile_source())


if __name__ == "__main__":
    unittest.main()
