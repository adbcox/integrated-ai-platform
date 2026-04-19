"""Tests for PHASE3-CONTEXT-BUNDLE-UNBLOCK-1: scored target ranking + relaxed prompt_ready gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.framework_control_plane import (
    _SAFE_BUNDLE_DEFAULTS,
    _phase2_derive_read_targets,
    _phase2_retrieval_summary,
    _phase3_assemble_context_bundle,
    _phase3_extract_symbol_index,
)


def _search_obs(matches: list[dict]) -> dict:
    return {
        "tool_name": "search",
        "status": "executed",
        "return_code": 0,
        "stdout": "",
        "structured_payload": {"query": "test", "match_count": len(matches), "matches": matches},
        "duration_ms": 0,
        "error": "",
    }


def _match(path: str, line: int = 1) -> dict:
    return {"path": path, "line_number": line, "line_text": "x"}


def _read_content(path: str, stdout: str, size_bytes: int = 0) -> dict:
    return {"path": path, "stdout": stdout, "size_bytes": size_bytes, "structured_payload": {}, "duration_ms": 0, "error": ""}


def _symbol_entry(path: str, classes=(), functions=(), methods=()) -> dict:
    sc = len(classes) + len(functions) + len(methods)
    return {"path": path, "classes": list(classes), "functions": list(functions), "methods": list(methods), "symbol_count": sc}


class TestDeriveReadTargetsBasic(unittest.TestCase):
    def test_returns_empty_on_empty_input(self):
        self.assertEqual(_phase2_derive_read_targets([]), [])

    def test_returns_list_on_valid_input(self):
        obs = _search_obs([_match("framework/worker_runtime.py")])
        result = _phase2_derive_read_targets([obs])
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_prefers_framework_over_init(self):
        obs = _search_obs([
            _match("__init__.py"),
            _match("framework/worker_runtime.py"),
        ])
        result = _phase2_derive_read_targets([obs], max_files=1)
        self.assertEqual(len(result), 1)
        self.assertIn("framework", result[0]["arguments"]["path"])

    def test_returns_empty_on_matches_lacking_path(self):
        obs = _search_obs([{"line_number": 1, "line_text": "x"}])
        result = _phase2_derive_read_targets([obs])
        self.assertEqual(result, [])

    def test_penalizes_pycache(self):
        obs = _search_obs([
            _match("__pycache__/worker_runtime.cpython-311.pyc"),
            _match("framework/worker_runtime.py"),
        ])
        result = _phase2_derive_read_targets([obs], max_files=1)
        self.assertNotIn("__pycache__", result[0]["arguments"]["path"])

    def test_frequency_breaks_ties(self):
        # framework/worker_runtime.py appears twice, tests/conftest.py once
        obs = _search_obs([
            _match("framework/worker_runtime.py"),
            _match("framework/worker_runtime.py"),
            _match("tests/conftest.py"),
        ])
        result = _phase2_derive_read_targets([obs], max_files=1)
        self.assertIn("worker_runtime", result[0]["arguments"]["path"])

    def test_respects_max_files(self):
        obs = _search_obs([_match(f"framework/file_{i}.py") for i in range(10)])
        result = _phase2_derive_read_targets([obs], max_files=3)
        self.assertLessEqual(len(result), 3)

    def test_no_exception_on_malformed_typed_results(self):
        for bad in [None, "string", 42, [None, {"tool_name": "search"}]]:
            try:
                _phase2_derive_read_targets(bad)
            except Exception as e:
                self.fail(f"raised on {bad!r}: {e}")


class TestRetrievalSummaryScored(unittest.TestCase):
    def test_top_match_file_is_highest_scoring_path(self):
        obs = _search_obs([
            _match("__init__.py"),
            _match("framework/job_schema.py"),
        ])
        summary = _phase2_retrieval_summary([obs], max_files=3)
        self.assertIn("framework", summary["top_match_file"])

    def test_unique_file_paths_in_scored_order(self):
        obs = _search_obs([
            _match("setup.py"),
            _match("framework/worker_runtime.py"),
        ])
        summary = _phase2_retrieval_summary([obs], max_files=3)
        paths = summary["unique_file_paths"]
        self.assertGreater(len(paths), 0)
        self.assertIn("framework", paths[0])


class TestExtractSymbolIndexMethods(unittest.TestCase):
    _SAMPLE = "class Foo:\n    def bar(self):\n        pass\n    def baz(self):\n        pass\n"

    def test_symbol_count_positive_for_class_with_methods(self):
        result = _phase3_extract_symbol_index([_read_content("x.py", self._SAMPLE)])
        self.assertGreater(result[0]["symbol_count"], 0)

    def test_returned_entry_contains_methods_key(self):
        result = _phase3_extract_symbol_index([_read_content("x.py", self._SAMPLE)])
        self.assertIn("methods", result[0])

    def test_methods_list_nonempty_for_indented_def(self):
        result = _phase3_extract_symbol_index([_read_content("x.py", self._SAMPLE)])
        self.assertGreater(len(result[0]["methods"]), 0)

    def test_top_level_functions_still_in_functions(self):
        src = "def top_func():\n    pass\n"
        result = _phase3_extract_symbol_index([_read_content("x.py", src)])
        self.assertIn("top_func", result[0]["functions"])

    def test_top_level_def_not_duplicated_in_methods(self):
        src = "def top_func():\n    pass\n"
        result = _phase3_extract_symbol_index([_read_content("x.py", src)])
        self.assertNotIn("top_func", result[0]["methods"])


class TestContextBundlePromptReady(unittest.TestCase):
    def _retrieval_summary(self, query: str = "test query") -> dict:
        return {
            "query": query,
            "search_match_count": 1,
            "unique_file_paths": ["framework/worker_runtime.py"],
            "top_match_file": "framework/worker_runtime.py",
            "top_match_line": 1,
            "search_truncated": False,
            "repo_map_entry_count": 0,
            "repo_map_truncated": False,
            "read_targets_derived": 1,
        }

    def test_prompt_ready_true_with_content_no_symbols(self):
        rc = [_read_content("framework/worker_runtime.py", "x" * 500, size_bytes=500)]
        si = [_symbol_entry("framework/worker_runtime.py")]
        bundle = _phase3_assemble_context_bundle(self._retrieval_summary(), rc, si)
        self.assertTrue(bundle["prompt_ready"])

    def test_prompt_ready_false_when_content_too_small_no_symbols(self):
        rc = [_read_content("x.py", "short", size_bytes=10)]
        si = [_symbol_entry("x.py")]
        bundle = _phase3_assemble_context_bundle(self._retrieval_summary(), rc, si)
        self.assertFalse(bundle["prompt_ready"])

    def test_total_content_chars_key_present(self):
        rc = [_read_content("x.py", "hello", size_bytes=5)]
        si = [_symbol_entry("x.py")]
        bundle = _phase3_assemble_context_bundle(self._retrieval_summary(), rc, si)
        self.assertIn("total_content_chars", bundle)

    def test_total_content_chars_equals_sum_size_bytes(self):
        rc = [
            _read_content("a.py", "x" * 300, size_bytes=300),
            _read_content("b.py", "y" * 200, size_bytes=200),
        ]
        si = [_symbol_entry("a.py"), _symbol_entry("b.py")]
        bundle = _phase3_assemble_context_bundle(self._retrieval_summary(), rc, si)
        self.assertEqual(bundle["total_content_chars"], 500)

    def test_prompt_ready_true_when_symbols_present(self):
        rc = [_read_content("x.py", "class Foo:\n    pass\n", size_bytes=20)]
        si = [_symbol_entry("x.py", classes=["Foo"])]
        bundle = _phase3_assemble_context_bundle(self._retrieval_summary(), rc, si)
        self.assertTrue(bundle["prompt_ready"])

    def test_prompt_ready_false_on_empty_symbol_index(self):
        bundle = _phase3_assemble_context_bundle(self._retrieval_summary(), [], [])
        self.assertFalse(bundle["prompt_ready"])

    def test_no_exception_on_empty_lists(self):
        try:
            _phase3_assemble_context_bundle({}, [], [])
        except Exception as e:
            self.fail(f"raised: {e}")


class TestSafeBundleDefaults(unittest.TestCase):
    def test_safe_bundle_defaults_contains_total_content_chars(self):
        self.assertIn("total_content_chars", _SAFE_BUNDLE_DEFAULTS)


class TestSourceTextAssertions(unittest.TestCase):
    def _src(self) -> str:
        return (REPO_ROOT / "framework" / "framework_control_plane.py").read_text()

    def test_derive_targets_low_value_names_in_source(self):
        self.assertIn("_DERIVE_TARGETS_LOW_VALUE_NAMES", self._src())

    def test_re_method_in_source(self):
        self.assertIn("_RE_METHOD", self._src())

    def test_total_content_chars_in_source(self):
        self.assertIn("total_content_chars", self._src())


if __name__ == "__main__":
    unittest.main()
