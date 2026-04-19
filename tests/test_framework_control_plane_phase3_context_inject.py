"""Tests for _phase3_build_context_prompt and context_bundle_probe wiring."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_build_context_prompt


def _bundle(
    query="_execute_job",
    total_files=1,
    top_file="framework/x.py",
    top_file_symbol_count=2,
    files=None,
):
    if files is None:
        files = [
            {"path": "framework/x.py", "classes": ["MyClass"], "functions": ["my_func"],
             "symbol_count": 2, "size_bytes": 100, "stdout_excerpt": "class MyClass:\n    pass"},
        ]
    return {
        "query": query,
        "total_files": total_files,
        "total_symbols": sum(f.get("symbol_count", 0) for f in files),
        "files_with_symbols": sum(1 for f in files if f.get("symbol_count", 0) > 0),
        "files": files,
        "top_file": top_file,
        "top_file_symbol_count": top_file_symbol_count,
        "prompt_ready": bool(query and total_files > 0),
    }


class TestBuildContextPromptEmpty(unittest.TestCase):
    def test_empty_dict_returns_empty(self):
        self.assertEqual(_phase3_build_context_prompt({}), "")

    def test_empty_query_returns_empty(self):
        b = _bundle(query="")
        self.assertEqual(_phase3_build_context_prompt(b), "")

    def test_total_files_zero_returns_empty(self):
        b = _bundle(total_files=0, files=[])
        self.assertEqual(_phase3_build_context_prompt(b), "")

    def test_non_dict_returns_empty_without_raise(self):
        self.assertEqual(_phase3_build_context_prompt(None), "")  # type: ignore[arg-type]
        self.assertEqual(_phase3_build_context_prompt("bad"), "")  # type: ignore[arg-type]


class TestBuildContextPromptContent(unittest.TestCase):
    def test_valid_bundle_returns_non_empty(self):
        result = _phase3_build_context_prompt(_bundle())
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_prompt_contains_query(self):
        result = _phase3_build_context_prompt(_bundle(query="_execute_job"))
        self.assertIn("_execute_job", result)

    def test_prompt_contains_file_path(self):
        result = _phase3_build_context_prompt(_bundle())
        self.assertIn("framework/x.py", result)

    def test_prompt_contains_class_name(self):
        result = _phase3_build_context_prompt(_bundle())
        self.assertIn("MyClass", result)

    def test_prompt_contains_function_name(self):
        result = _phase3_build_context_prompt(_bundle())
        self.assertIn("my_func", result)

    def test_prompt_shows_total_files_count(self):
        files = [
            {"path": "a.py", "classes": ["A"], "functions": [], "symbol_count": 1,
             "size_bytes": 10, "stdout_excerpt": ""},
            {"path": "b.py", "classes": [], "functions": ["b"], "symbol_count": 1,
             "size_bytes": 10, "stdout_excerpt": ""},
        ]
        b = _bundle(query="q", total_files=2, top_file="a.py", top_file_symbol_count=1, files=files)
        result = _phase3_build_context_prompt(b)
        self.assertIn("Retrieved 2 file(s)", result)

    def test_classes_capped_at_10_unique(self):
        classes = [f"Class{i}" for i in range(15)]
        files = [{"path": "x.py", "classes": classes, "functions": [],
                  "symbol_count": len(classes), "size_bytes": 100, "stdout_excerpt": ""}]
        b = _bundle(query="q", total_files=1, files=files)
        result = _phase3_build_context_prompt(b)
        present = sum(1 for c in classes if c in result)
        self.assertLessEqual(present, 10)

    def test_functions_capped_at_10_unique(self):
        funcs = [f"func_{i}" for i in range(15)]
        files = [{"path": "x.py", "classes": [], "functions": funcs,
                  "symbol_count": len(funcs), "size_bytes": 100, "stdout_excerpt": ""}]
        b = _bundle(query="q", total_files=1, files=files)
        result = _phase3_build_context_prompt(b)
        present = sum(1 for f in funcs if f in result)
        self.assertLessEqual(present, 10)

    def test_duplicate_class_names_deduplicated(self):
        files = [
            {"path": "a.py", "classes": ["Dup"], "functions": [], "symbol_count": 1,
             "size_bytes": 10, "stdout_excerpt": ""},
            {"path": "b.py", "classes": ["Dup"], "functions": [], "symbol_count": 1,
             "size_bytes": 10, "stdout_excerpt": ""},
        ]
        b = _bundle(query="q", total_files=2, files=files)
        result = _phase3_build_context_prompt(b)
        self.assertEqual(result.count("Dup"), 1)

    def test_none_for_classes_when_no_classes(self):
        files = [{"path": "x.py", "classes": [], "functions": ["f"],
                  "symbol_count": 1, "size_bytes": 10, "stdout_excerpt": ""}]
        b = _bundle(query="q", total_files=1, files=files)
        result = _phase3_build_context_prompt(b)
        self.assertIn("(none)", result)

    def test_none_for_functions_when_no_functions(self):
        files = [{"path": "x.py", "classes": ["C"], "functions": [],
                  "symbol_count": 1, "size_bytes": 10, "stdout_excerpt": ""}]
        b = _bundle(query="q", total_files=1, files=files)
        result = _phase3_build_context_prompt(b)
        self.assertIn("(none)", result)


class TestLoadContextBundle(unittest.TestCase):
    def test_nonexistent_path_returns_empty(self):
        from bin.framework_control_plane import _load_context_bundle
        result = _load_context_bundle(Path("/tmp/__nonexistent_cb__.json"))
        self.assertEqual(result, {})

    def test_valid_json_returns_dict(self):
        from bin.framework_control_plane import _load_context_bundle
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"query": "test", "total_files": 1}, f)
            tmp_path = Path(f.name)
        try:
            result = _load_context_bundle(tmp_path)
            self.assertEqual(result.get("query"), "test")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_malformed_json_returns_empty(self):
        from bin.framework_control_plane import _load_context_bundle
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not valid json")
            tmp_path = Path(f.name)
        try:
            result = _load_context_bundle(tmp_path)
            self.assertEqual(result, {})
        finally:
            tmp_path.unlink(missing_ok=True)


class TestContextInjectMeta(unittest.TestCase):
    def test_importable_from_framework(self):
        from framework.framework_control_plane import _phase3_build_context_prompt as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_build_context_prompt", m.__all__)


if __name__ == "__main__":
    unittest.main()
