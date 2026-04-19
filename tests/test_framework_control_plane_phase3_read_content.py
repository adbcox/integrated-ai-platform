"""Tests for _phase3_extract_read_content and _phase3_read_content_summary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import (
    _phase3_extract_read_content,
    _phase3_read_content_summary,
)

_REQUIRED_EXTRACT_KEYS = {"path", "stdout", "size_bytes", "structured_payload", "duration_ms", "error"}
_REQUIRED_SUMMARY_KEYS = {"files_read", "file_paths", "total_bytes", "top_file", "top_file_bytes", "any_errors"}


def _read_obs(
    *,
    path="framework/x.py",
    stdout="content here",
    size_bytes=None,
    status="executed",
    duration_ms=10,
    error="",
):
    sp: dict = {"path": path}
    if size_bytes is not None:
        sp["size_bytes"] = size_bytes
    return {
        "tool_name": "read_file",
        "status": status,
        "stdout": stdout,
        "structured_payload": sp,
        "duration_ms": duration_ms,
        "error": error,
        "return_code": 0,
    }


def _search_obs(path="a.py"):
    return {
        "tool_name": "search",
        "status": "executed",
        "stdout": "",
        "structured_payload": {"matches": [{"path": path, "line_number": 1, "line_text": ""}]},
        "duration_ms": 1,
        "error": "",
        "return_code": 0,
    }


class TestExtractReadContentEmpty(unittest.TestCase):
    def test_empty_list_returns_empty(self):
        self.assertEqual(_phase3_extract_read_content([]), [])

    def test_non_read_file_observations_excluded(self):
        self.assertEqual(_phase3_extract_read_content([_search_obs()]), [])

    def test_failed_read_excluded(self):
        obs = _read_obs(status="blocked")
        self.assertEqual(_phase3_extract_read_content([obs]), [])

    def test_non_dict_entries_skipped_without_raise(self):
        result = _phase3_extract_read_content([None, "bad", _read_obs()])
        self.assertEqual(len(result), 1)

    def test_empty_input_no_exception(self):
        try:
            result = _phase3_extract_read_content([])
            self.assertIsInstance(result, list)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")


class TestExtractReadContent(unittest.TestCase):
    def test_path_extracted_from_structured_payload(self):
        obs = _read_obs(path="framework/worker_runtime.py", stdout="abc")
        result = _phase3_extract_read_content([obs])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "framework/worker_runtime.py")

    def test_stdout_preserved(self):
        obs = _read_obs(stdout="hello world")
        result = _phase3_extract_read_content([obs])
        self.assertEqual(result[0]["stdout"], "hello world")

    def test_size_bytes_from_structured_payload(self):
        obs = _read_obs(stdout="abc", size_bytes=999)
        result = _phase3_extract_read_content([obs])
        self.assertEqual(result[0]["size_bytes"], 999)

    def test_size_bytes_falls_back_to_len_stdout(self):
        obs = _read_obs(stdout="hello", size_bytes=None)
        result = _phase3_extract_read_content([obs])
        self.assertEqual(result[0]["size_bytes"], 5)

    def test_result_dict_has_all_required_keys(self):
        obs = _read_obs()
        result = _phase3_extract_read_content([obs])
        self.assertEqual(set(result[0].keys()), _REQUIRED_EXTRACT_KEYS)

    def test_multiple_read_observations_all_returned(self):
        obs1 = _read_obs(path="a.py", stdout="aaa")
        obs2 = _read_obs(path="b.py", stdout="bb")
        result = _phase3_extract_read_content([obs1, obs2])
        self.assertEqual(len(result), 2)
        paths = [r["path"] for r in result]
        self.assertIn("a.py", paths)
        self.assertIn("b.py", paths)

    def test_error_field_preserved(self):
        obs = _read_obs(error="permission denied")
        result = _phase3_extract_read_content([obs])
        self.assertEqual(result[0]["error"], "permission denied")


class TestReadContentSummary(unittest.TestCase):
    def test_empty_returns_all_required_keys(self):
        s = _phase3_read_content_summary([])
        self.assertEqual(set(s.keys()), _REQUIRED_SUMMARY_KEYS)

    def test_empty_returns_safe_defaults(self):
        s = _phase3_read_content_summary([])
        self.assertEqual(s["files_read"], 0)
        self.assertEqual(s["file_paths"], [])
        self.assertEqual(s["total_bytes"], 0)
        self.assertEqual(s["top_file"], "")
        self.assertEqual(s["top_file_bytes"], 0)
        self.assertFalse(s["any_errors"])

    def test_files_read_correct_count(self):
        obs1 = _read_obs(path="a.py", stdout="aaa")
        obs2 = _read_obs(path="b.py", stdout="bb")
        s = _phase3_read_content_summary([obs1, obs2])
        self.assertEqual(s["files_read"], 2)

    def test_total_bytes_correct_sum(self):
        obs1 = _read_obs(stdout="abc", size_bytes=3)
        obs2 = _read_obs(path="b.py", stdout="de", size_bytes=2)
        s = _phase3_read_content_summary([obs1, obs2])
        self.assertEqual(s["total_bytes"], 5)

    def test_top_file_is_first_path(self):
        obs1 = _read_obs(path="first.py", stdout="x", size_bytes=1)
        obs2 = _read_obs(path="second.py", stdout="yy", size_bytes=2)
        s = _phase3_read_content_summary([obs1, obs2])
        self.assertEqual(s["top_file"], "first.py")
        self.assertEqual(s["top_file_bytes"], 1)

    def test_any_errors_true_when_error_present(self):
        obs = _read_obs(error="read failed")
        s = _phase3_read_content_summary([obs])
        self.assertTrue(s["any_errors"])

    def test_file_paths_capped_at_max_files(self):
        observations = [_read_obs(path=f"f{i}.py", stdout="x") for i in range(10)]
        s = _phase3_read_content_summary(observations, max_files=3)
        self.assertEqual(len(s["file_paths"]), 3)

    def test_both_helpers_in_all(self):
        from framework import framework_control_plane as m
        self.assertIn("_phase3_extract_read_content", m.__all__)
        self.assertIn("_phase3_read_content_summary", m.__all__)


if __name__ == "__main__":
    unittest.main()
