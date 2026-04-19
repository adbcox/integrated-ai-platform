"""Tests for _phase3_build_recommendation in framework/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_build_recommendation

_REQUIRED_KEYS = {"query", "inference_text", "files_analyzed", "symbol_count", "top_file", "chars", "recommendation_ready"}


def _bundle(query: str = "", total_files: int = 0, total_symbols: int = 0, top_file: str = "") -> dict:
    return {"query": query, "total_files": total_files, "total_symbols": total_symbols, "top_file": top_file}


def _inference(output_text: str = "", has_content: bool = False) -> dict:
    return {"output_text": output_text, "has_content": has_content}


class TestPhase3BuildRecommendation(unittest.TestCase):
    def test_returns_dict_with_all_required_keys_on_empty_inputs(self):
        result = _phase3_build_recommendation({}, {})
        self.assertEqual(set(result.keys()), _REQUIRED_KEYS)

    def test_recommendation_ready_false_on_empty_inputs(self):
        self.assertFalse(_phase3_build_recommendation({}, {})["recommendation_ready"])

    def test_recommendation_ready_true_when_query_and_content(self):
        result = _phase3_build_recommendation(
            _bundle(query="WorkerRuntime job execution"),
            _inference(output_text="The WorkerRuntime schedules jobs via...", has_content=True),
        )
        self.assertTrue(result["recommendation_ready"])

    def test_query_extracted_from_context_bundle(self):
        result = _phase3_build_recommendation(
            _bundle(query="ExecutorFactory usage"),
            _inference(output_text="some content"),
        )
        self.assertEqual(result["query"], "ExecutorFactory usage")

    def test_inference_text_matches_output_text(self):
        text = "The scheduler processes jobs in FIFO order."
        result = _phase3_build_recommendation({}, _inference(output_text=text))
        self.assertEqual(result["inference_text"], text)

    def test_files_analyzed_matches_total_files(self):
        result = _phase3_build_recommendation(_bundle(total_files=7), {})
        self.assertEqual(result["files_analyzed"], 7)

    def test_symbol_count_matches_total_symbols(self):
        result = _phase3_build_recommendation(_bundle(total_symbols=42), {})
        self.assertEqual(result["symbol_count"], 42)

    def test_top_file_matches_context_bundle_top_file(self):
        result = _phase3_build_recommendation(_bundle(top_file="framework/worker_runtime.py"), {})
        self.assertEqual(result["top_file"], "framework/worker_runtime.py")

    def test_chars_equals_len_of_inference_text(self):
        text = "hello world"
        result = _phase3_build_recommendation({}, _inference(output_text=text))
        self.assertEqual(result["chars"], len(text))

    def test_recommendation_ready_false_when_query_empty(self):
        result = _phase3_build_recommendation(
            _bundle(query=""),
            _inference(output_text="some content"),
        )
        self.assertFalse(result["recommendation_ready"])

    def test_recommendation_ready_false_when_output_text_whitespace_only(self):
        result = _phase3_build_recommendation(
            _bundle(query="something"),
            _inference(output_text="   \n\t  "),
        )
        self.assertFalse(result["recommendation_ready"])

    def test_no_exception_on_non_dict_context_bundle(self):
        try:
            result = _phase3_build_recommendation("not a dict", {})
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_non_dict_inference_response(self):
        try:
            result = _phase3_build_recommendation({}, 42)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")

    def test_no_exception_on_none_inputs(self):
        try:
            result = _phase3_build_recommendation(None, None)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")


class TestSourceTextAssertions(unittest.TestCase):
    def _framework_source(self):
        return (Path(__file__).resolve().parents[1] / "framework" / "framework_control_plane.py").read_text()

    def _bin_source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def test_phase3_build_recommendation_in_framework_source(self):
        self.assertIn("_phase3_build_recommendation", self._framework_source())

    def test_phase3_query_in_bin_source(self):
        self.assertIn("--phase3-query", self._bin_source())

    def test_phase3_recommendation_persisted_in_bin_source(self):
        self.assertIn("phase3_recommendation_persisted", self._bin_source())

    def test_retrieval_probe_template_importable(self):
        from bin.framework_control_plane import _retrieval_probe_template
        self.assertTrue(callable(_retrieval_probe_template))


if __name__ == "__main__":
    unittest.main()
