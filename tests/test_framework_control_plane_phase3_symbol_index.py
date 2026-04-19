"""Tests for _phase3_extract_symbol_index."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase3_extract_symbol_index


def _entry(path="framework/x.py", stdout=""):
    return {
        "path": path,
        "stdout": stdout,
        "size_bytes": len(stdout),
        "structured_payload": {"path": path},
        "duration_ms": 1,
        "error": "",
    }


class TestSymbolIndexEmpty(unittest.TestCase):
    def test_empty_list_returns_empty(self):
        self.assertEqual(_phase3_extract_symbol_index([]), [])

    def test_non_list_input_returns_empty(self):
        self.assertEqual(_phase3_extract_symbol_index(None), [])  # type: ignore[arg-type]

    def test_single_entry_no_symbols(self):
        result = _phase3_extract_symbol_index([_entry(stdout="")])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["classes"], [])
        self.assertEqual(result[0]["functions"], [])
        self.assertEqual(result[0]["symbol_count"], 0)

    def test_non_dict_entry_skipped_without_raise(self):
        result = _phase3_extract_symbol_index([None, _entry(stdout="def foo():\n    pass\n")])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["functions"], ["foo"])

    def test_does_not_raise_on_malformed_input(self):
        try:
            result = _phase3_extract_symbol_index(["bad", 42, None])
            self.assertIsInstance(result, list)
        except Exception as e:
            self.fail(f"Raised unexpected exception: {e}")


class TestSymbolIndexExtraction(unittest.TestCase):
    def test_single_class(self):
        result = _phase3_extract_symbol_index([_entry(stdout="class Foo:\n    pass\n")])
        self.assertIn("Foo", result[0]["classes"])
        self.assertEqual(result[0]["symbol_count"], 1)

    def test_single_def(self):
        result = _phase3_extract_symbol_index([_entry(stdout="def bar():\n    pass\n")])
        self.assertIn("bar", result[0]["functions"])
        self.assertEqual(result[0]["symbol_count"], 1)

    def test_multiple_classes_and_functions(self):
        stdout = "class A:\n    pass\nclass B:\n    pass\ndef f1():\n    pass\ndef f2():\n    pass\n"
        result = _phase3_extract_symbol_index([_entry(stdout=stdout)])
        self.assertEqual(result[0]["classes"], ["A", "B"])
        self.assertEqual(result[0]["functions"], ["f1", "f2"])
        self.assertEqual(result[0]["symbol_count"], 4)

    def test_class_deduplication(self):
        stdout = "class X:\n    pass\nclass X:\n    pass\n"
        result = _phase3_extract_symbol_index([_entry(stdout=stdout)])
        self.assertEqual(result[0]["classes"], ["X"])

    def test_def_deduplication(self):
        stdout = "def helper():\n    pass\ndef helper():\n    pass\n"
        result = _phase3_extract_symbol_index([_entry(stdout=stdout)])
        self.assertEqual(result[0]["functions"], ["helper"])

    def test_class_mid_line_not_matched(self):
        stdout = "x = class_factory()\nsome_class = 1\n"
        result = _phase3_extract_symbol_index([_entry(stdout=stdout)])
        self.assertEqual(result[0]["classes"], [])

    def test_indented_def_not_matched(self):
        stdout = "class Foo:\n    def method(self):\n        pass\n"
        result = _phase3_extract_symbol_index([_entry(stdout=stdout)])
        self.assertEqual(result[0]["classes"], ["Foo"])
        self.assertEqual(result[0]["functions"], [])

    def test_stdout_non_string_coerced(self):
        entry = {"path": "x.py", "stdout": 12345, "size_bytes": 0,
                 "structured_payload": {}, "duration_ms": 0, "error": ""}
        try:
            result = _phase3_extract_symbol_index([entry])
            self.assertIsInstance(result, list)
        except Exception as e:
            self.fail(f"Raised on non-string stdout: {e}")

    def test_path_absent_defaults_to_empty_string(self):
        entry = {"stdout": "def f():\n    pass\n", "size_bytes": 0,
                 "structured_payload": {}, "duration_ms": 0, "error": ""}
        result = _phase3_extract_symbol_index([entry])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "")

    def test_multiple_entries_same_length(self):
        entries = [
            _entry(path="a.py", stdout="class A:\n    pass\n"),
            _entry(path="b.py", stdout="def b():\n    pass\n"),
        ]
        result = _phase3_extract_symbol_index(entries)
        self.assertEqual(len(result), 2)

    def test_importable_from_framework(self):
        from framework.framework_control_plane import _phase3_extract_symbol_index as fn
        self.assertTrue(callable(fn))

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_phase3_extract_symbol_index", m.__all__)


if __name__ == "__main__":
    unittest.main()
