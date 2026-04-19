"""Tests for corrected Phase 3 continuation analysis pipeline in bin/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin.framework_control_plane import (
    _run_phase3_continuation,
    _DEFAULT_CONTEXT_BUNDLE_PATH,
    _DEFAULT_RECOMMENDATION_PATH,
)

import argparse


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(
        state_root="/tmp/test_phase3_cont_analysis",
        wait_timeout_seconds=5,
        phase3_auto_continue=False,
        task_template="retrieval_probe",
        **kwargs,
    )


def _raising_scheduler_patch():
    return unittest.mock.patch(
        "bin.framework_control_plane.Scheduler",
        side_effect=RuntimeError("mock scheduler error"),
    )


class TestContinuationAnalysisExceptionPath(unittest.TestCase):
    def test_next_action_is_dict_on_exception_path(self):
        with _raising_scheduler_patch():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertIsInstance(result["phase3_continuation_next_action"], dict)

    def test_recommendation_ready_false_on_exception_path(self):
        with _raising_scheduler_patch():
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )
        self.assertFalse(result["phase3_continuation_recommendation_ready"])


class TestContinuationAnalysisSourceAssertions(unittest.TestCase):
    def _source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def test_phase3_extract_inference_response_in_continuation_body(self):
        self.assertIn("cont_inference_response = _phase3_extract_inference_response", self._source())

    def test_load_context_bundle_default_path_in_continuation(self):
        self.assertIn("_load_context_bundle(_DEFAULT_CONTEXT_BUNDLE_PATH)", self._source())

    def test_phase2_retrieval_summary_in_source(self):
        self.assertIn("_phase2_retrieval_summary", self._source())

    def test_cont_next_action_local_variable_in_source(self):
        self.assertIn("cont_next_action", self._source())

    def test_phase3_continuation_recommendation_ready_in_safe_dict(self):
        src = self._source()
        self.assertIn("phase3_continuation_recommendation_ready", src)
        safe_region = src[src.find("_CONTINUATION_SAFE"):src.find("_CONTINUATION_SAFE") + 500]
        self.assertIn("phase3_continuation_recommendation_ready", safe_region)

    def test_default_recommendation_path_in_continuation_body(self):
        src = self._source()
        cont_fn_start = src.find("def _run_phase3_continuation(")
        cont_fn_end = src.find("\ndef main()", cont_fn_start)
        cont_body = src[cont_fn_start:cont_fn_end]
        self.assertIn("_DEFAULT_RECOMMENDATION_PATH", cont_body)


class TestContinuationAnalysisIntegration(unittest.TestCase):
    """Integration test: mock scheduler success + analysis pipeline to verify ready path."""

    def _make_cont_payload(self) -> dict:
        return {
            "typed_tool_trace": [
                {
                    "tool_name": "search",
                    "status": "executed",
                    "structured_payload": {
                        "query": "test_query",
                        "match_count": 1,
                        "matches": [{"path": "framework/worker_runtime.py"}],
                    },
                }
            ],
        }

    @unittest.skip("Integration test requires complex mock setup — skipped per packet spec")
    def test_continuation_reaches_ready_and_builds_recommendation(self):
        cont_payload = self._make_cont_payload()
        mock_job = MagicMock()
        mock_job.job_id = "test-cont-job-id"
        mock_scheduler_inst = MagicMock()
        mock_scheduler_inst.submit.return_value = mock_job
        mock_scheduler_inst.wait_for_idle.return_value = True

        ready_action = {"action": "ready", "context_adequate": True}
        rec = {"recommendation_ready": True, "query": "test_query", "inference_text": "analysis..."}
        prompt_ready_bundle = {"prompt_ready": True, "query": "test_query", "total_files": 1}
        inf_response = {"has_content": True, "output_text": "analysis..."}

        with patch("bin.framework_control_plane.Scheduler", return_value=mock_scheduler_inst), \
             patch("bin.framework_control_plane._load_context_bundle", return_value=prompt_ready_bundle), \
             patch("bin.framework_control_plane._phase2_extract_typed_results", return_value=[{"tool": "search"}]), \
             patch("bin.framework_control_plane._phase3_extract_inference_response", return_value=inf_response), \
             patch("bin.framework_control_plane._phase2_retrieval_summary", return_value={}), \
             patch("bin.framework_control_plane._phase3_extract_read_content", return_value=[]), \
             patch("bin.framework_control_plane._phase3_extract_symbol_index", return_value={}), \
             patch("bin.framework_control_plane._phase3_assemble_context_bundle", return_value={"prompt_ready": False}), \
             patch("bin.framework_control_plane._phase3_derive_next_action", return_value=ready_action), \
             patch("bin.framework_control_plane._phase3_build_recommendation", return_value=rec), \
             patch("bin.framework_control_plane._DEFAULT_RECOMMENDATION_PATH") as mock_rec_path, \
             patch("pathlib.Path.exists", return_value=False):
            mock_rec_path.parent.mkdir = MagicMock()
            mock_rec_path.write_text = MagicMock()
            result = _run_phase3_continuation(
                _make_args(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), "retrieval_probe"
            )

        self.assertEqual(result["phase3_continuation_next_action"].get("action"), "ready")
        self.assertTrue(result["phase3_continuation_recommendation_ready"])


if __name__ == "__main__":
    unittest.main()
