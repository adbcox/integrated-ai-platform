"""Tests for _run_post_apply_validation in bin/stage3_manager.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.stage3_manager import _run_post_apply_validation  # noqa: E402


class PostApplyValidationTest(unittest.TestCase):
    def test_valid_py_file_returns_syntax_ok(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = 1\n")
            path = f.name
        ok, note = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertTrue(ok)
        self.assertEqual(note, "syntax_ok")

    def test_invalid_py_file_returns_syntax_error(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def f(\n")
            path = f.name
        ok, note = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertFalse(ok)
        self.assertTrue(note.startswith("syntax_error:"), note)

    def test_sh_file_returns_no_validation_for_filetype(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".sh", mode="w", delete=False) as f:
            f.write("#!/bin/bash\necho hi\n")
            path = f.name
        ok, note = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertTrue(ok)
        self.assertEqual(note, "no_validation_for_filetype")

    def test_json_file_returns_no_validation_for_filetype(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write('{"key": "value"}\n')
            path = f.name
        ok, note = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertTrue(ok)
        self.assertEqual(note, "no_validation_for_filetype")

    def test_nonexistent_path_returns_false_tuple_no_raise(self) -> None:
        ok, note = _run_post_apply_validation("/tmp/nonexistent_xyzzy_12345.py")
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)
        self.assertFalse(ok)

    def test_empty_py_file_returns_syntax_ok(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("")
            path = f.name
        ok, note = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertTrue(ok)
        self.assertEqual(note, "syntax_ok")

    def test_return_value_is_always_2_tuple(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("a = 1\n")
            path = f.name
        result = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_first_element_is_bool_second_is_str(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("pass\n")
            path = f.name
        ok, note = _run_post_apply_validation(path)
        Path(path).unlink(missing_ok=True)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)

    def test_function_exists_in_source(self) -> None:
        source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")
        self.assertIn("_run_post_apply_validation", source)

    def test_trace_fields_exist_in_source(self) -> None:
        source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")
        self.assertIn("post_apply_validation_status", source)
        self.assertIn("post_apply_validation_note", source)


if __name__ == "__main__":
    unittest.main()
