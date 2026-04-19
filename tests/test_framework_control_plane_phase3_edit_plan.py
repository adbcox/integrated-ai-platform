"""Tests for _phase3_build_edit_plan in framework/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_build_edit_plan

_REQUIRED_KEYS = {"query", "target_file", "plan_text", "has_replacement_format", "plan_ready", "chars"}


def _inference(output_text: str = "", has_content: bool = False) -> dict:
    return {"output_text": output_text, "has_content": has_content}


def _rec(query: str = "", top_file: str = "", recommendation_ready: bool = False) -> dict:
    return {"query": query, "top_file": top_file, "recommendation_ready": recommendation_ready}


class TestPhase3BuildEditPlanImport(unittest.TestCase):
    def test_importable_and_callable(self):
        self.assertTrue(callable(_phase3_build_edit_plan))


class TestPhase3BuildEditPlanReturnKeys(unittest.TestCase):
    def test_returns_dict_on_empty_inputs(self):
        self.assertIsInstance(_phase3_build_edit_plan({}, {}), dict)

    def test_all_required_keys_present_on_empty_inputs(self):
        result = _phase3_build_edit_plan({}, {})
        self.assertEqual(set(result.keys()), _REQUIRED_KEYS)

    def test_plan_ready_false_on_empty_inference(self):
        self.assertFalse(_phase3_build_edit_plan({}, {})["plan_ready"])

    def test_plan_ready_false_when_content_but_no_top_file(self):
        result = _phase3_build_edit_plan(_inference(output_text="some plan text"), _rec(query="q"))
        self.assertFalse(result["plan_ready"])

    def test_plan_ready_true_when_both_content_and_top_file(self):
        result = _phase3_build_edit_plan(
            _inference(output_text="framework/foo.py:: replace exact text 'old' with 'new'"),
            _rec(query="fix foo", top_file="framework/foo.py"),
        )
        self.assertTrue(result["plan_ready"])

    def test_target_file_extracted_from_recommendation_top_file(self):
        result = _phase3_build_edit_plan({}, _rec(top_file="framework/worker_runtime.py"))
        self.assertEqual(result["target_file"], "framework/worker_runtime.py")

    def test_query_extracted_from_recommendation_query(self):
        result = _phase3_build_edit_plan({}, _rec(query="ExecutorFactory usage"))
        self.assertEqual(result["query"], "ExecutorFactory usage")

    def test_has_replacement_format_true_for_valid_instruction(self):
        plan = "framework/foo.py:: replace exact text 'old_value' with 'new_value'"
        result = _phase3_build_edit_plan(_inference(output_text=plan), {})
        self.assertTrue(result["has_replacement_format"])

    def test_has_replacement_format_false_for_plain_prose(self):
        result = _phase3_build_edit_plan(_inference(output_text="This function does X and Y."), {})
        self.assertFalse(result["has_replacement_format"])

    def test_chars_equals_len_of_plan_text(self):
        text = "framework/foo.py:: replace exact text 'a' with 'b'"
        result = _phase3_build_edit_plan(_inference(output_text=text), {})
        self.assertEqual(result["chars"], len(text))

    def test_no_exception_on_non_dict_inference_response(self):
        try:
            result = _phase3_build_edit_plan("not a dict", {})
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_non_dict_recommendation(self):
        try:
            result = _phase3_build_edit_plan({}, 42)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_none_inputs(self):
        try:
            result = _phase3_build_edit_plan(None, None)
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

    def test_phase3_build_edit_plan_in_framework_source(self):
        self.assertIn("_phase3_build_edit_plan", self._framework_source())

    def test_phase3_edit_plan_probe_in_bin_task_template_choices(self):
        self.assertIn("phase3_edit_plan_probe", self._bin_source())

    def test_phase3_edit_plan_latest_json_in_bin_source(self):
        self.assertIn("phase3_edit_plan_latest.json", self._bin_source())

    def test_phase3_edit_plan_in_makefile(self):
        self.assertIn("phase3-edit-plan", self._makefile())


if __name__ == "__main__":
    unittest.main()
