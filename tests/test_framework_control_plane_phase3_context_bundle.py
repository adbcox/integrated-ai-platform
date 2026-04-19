"""Tests for _phase3_assemble_context_bundle."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_assemble_context_bundle

_BUNDLE_KEYS = {"query", "total_files", "total_symbols", "files_with_symbols",
                "files", "top_file", "top_file_symbol_count", "prompt_ready"}
_FILE_KEYS = {"path", "classes", "functions", "symbol_count", "size_bytes", "stdout_excerpt"}


def _retrieval_summary(query="_execute_job"):
    return {"query": query}


def _rc(path, stdout="content", size_bytes=None):
    return {
        "path": path,
        "stdout": stdout,
        "size_bytes": size_bytes if size_bytes is not None else len(stdout),
        "structured_payload": {},
        "duration_ms": 1,
        "error": "",
    }


def _sym(path, classes=None, functions=None):
    c = list(classes or [])
    f = list(functions or [])
    return {"path": path, "classes": c, "functions": f, "symbol_count": len(c) + len(f)}


class TestContextBundleEmpty(unittest.TestCase):
    def test_empty_inputs_returns_safe_defaults(self):
        b = _phase3_assemble_context_bundle({}, [], [])
        self.assertEqual(set(b.keys()), _BUNDLE_KEYS)
        self.assertEqual(b["total_files"], 0)
        self.assertEqual(b["total_symbols"], 0)
        self.assertEqual(b["files_with_symbols"], 0)
        self.assertEqual(b["files"], [])
        self.assertEqual(b["top_file"], "")
        self.assertEqual(b["top_file_symbol_count"], 0)
        self.assertFalse(b["prompt_ready"])

    def test_non_dict_retrieval_summary_returns_safe_defaults(self):
        b = _phase3_assemble_context_bundle(None, [], [])  # type: ignore[arg-type]
        self.assertEqual(set(b.keys()), _BUNDLE_KEYS)
        self.assertFalse(b["prompt_ready"])

    def test_non_list_symbol_index_returns_safe_defaults(self):
        b = _phase3_assemble_context_bundle({}, [], "bad")  # type: ignore[arg-type]
        self.assertEqual(set(b.keys()), _BUNDLE_KEYS)

    def test_top_file_empty_when_symbol_index_empty(self):
        b = _phase3_assemble_context_bundle(_retrieval_summary(), [], [])
        self.assertEqual(b["top_file"], "")


class TestContextBundleCounts(unittest.TestCase):
    def test_total_files_equals_symbol_index_length(self):
        syms = [_sym("a.py", classes=["A"]), _sym("b.py", functions=["f"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary(), [], syms)
        self.assertEqual(b["total_files"], 2)

    def test_total_symbols_correct_sum(self):
        syms = [_sym("a.py", classes=["A", "B"], functions=["f"]),
                _sym("b.py", functions=["g", "h"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary(), [], syms)
        self.assertEqual(b["total_symbols"], 5)

    def test_files_with_symbols_counts_nonzero_only(self):
        syms = [_sym("a.py", classes=["A"]), _sym("b.py")]
        b = _phase3_assemble_context_bundle(_retrieval_summary(), [], syms)
        self.assertEqual(b["files_with_symbols"], 1)

    def test_query_taken_from_retrieval_summary(self):
        b = _phase3_assemble_context_bundle(_retrieval_summary("my_query"), [], [])
        self.assertEqual(b["query"], "my_query")


class TestContextBundleTopFile(unittest.TestCase):
    def test_top_file_is_highest_symbol_count(self):
        syms = [_sym("a.py", classes=["A"]), _sym("b.py", classes=["X", "Y"], functions=["f"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary(), [], syms)
        self.assertEqual(b["top_file"], "b.py")
        self.assertEqual(b["top_file_symbol_count"], 3)

    def test_top_file_tie_first_occurrence_wins(self):
        syms = [_sym("first.py", classes=["A"]), _sym("second.py", functions=["b"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary(), [], syms)
        self.assertEqual(b["top_file"], "first.py")


class TestContextBundlePromptReady(unittest.TestCase):
    def test_prompt_ready_true_when_query_files_symbols(self):
        syms = [_sym("a.py", classes=["A"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary("q"), [], syms)
        self.assertTrue(b["prompt_ready"])

    def test_prompt_ready_false_when_query_empty(self):
        syms = [_sym("a.py", classes=["A"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary(""), [], syms)
        self.assertFalse(b["prompt_ready"])

    def test_prompt_ready_false_when_total_symbols_zero(self):
        syms = [_sym("a.py")]
        b = _phase3_assemble_context_bundle(_retrieval_summary("q"), [], syms)
        self.assertFalse(b["prompt_ready"])


class TestContextBundleJoin(unittest.TestCase):
    def test_size_bytes_joined_from_read_content(self):
        rcs = [_rc("framework/x.py", stdout="hello", size_bytes=99)]
        syms = [_sym("framework/x.py", classes=["Foo"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary("q"), rcs, syms)
        self.assertEqual(b["files"][0]["size_bytes"], 99)

    def test_stdout_excerpt_first_300_chars(self):
        long_stdout = "x" * 500
        rcs = [_rc("a.py", stdout=long_stdout)]
        syms = [_sym("a.py", classes=["A"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary("q"), rcs, syms)
        self.assertEqual(len(b["files"][0]["stdout_excerpt"]), 300)

    def test_stdout_excerpt_empty_when_path_not_in_read_content(self):
        syms = [_sym("missing.py", classes=["A"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary("q"), [], syms)
        self.assertEqual(b["files"][0]["stdout_excerpt"], "")

    def test_files_entry_has_all_required_keys(self):
        rcs = [_rc("x.py", stdout="def f():\n    pass\n")]
        syms = [_sym("x.py", functions=["f"])]
        b = _phase3_assemble_context_bundle(_retrieval_summary("q"), rcs, syms)
        self.assertEqual(set(b["files"][0].keys()), _FILE_KEYS)

    def test_importable_from_framework(self):
        from framework.framework_control_plane import _phase3_assemble_context_bundle as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_assemble_context_bundle", m.__all__)


if __name__ == "__main__":
    unittest.main()
