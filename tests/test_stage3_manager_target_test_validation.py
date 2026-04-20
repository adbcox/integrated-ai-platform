"""Tests for _discover_target_tests and _run_target_tests in bin/stage3_manager.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.stage3_manager import _discover_target_tests, _run_target_tests  # noqa: E402

TESTS_DIR = REPO_ROOT / "tests"


class DiscoverTargetTestsTest(unittest.TestCase):
    def test_no_match_stem_returns_empty(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            result = _discover_target_tests("framework/xyzzy_nonexistent_module.py", tests_dir=Path(td))
        self.assertEqual(result, [])

    def test_worker_runtime_returns_nonempty(self) -> None:
        result = _discover_target_tests("framework/worker_runtime.py")
        self.assertGreater(len(result), 0)

    def test_all_results_are_strings(self) -> None:
        result = _discover_target_tests("framework/worker_runtime.py")
        for item in result:
            self.assertIsInstance(item, str)

    def test_nonexistent_tests_dir_returns_empty_no_raise(self) -> None:
        result = _discover_target_tests("framework/worker_runtime.py", tests_dir=Path("/nonexistent/xyzzy"))
        self.assertEqual(result, [])

    def test_empty_target_does_not_raise_returns_list(self) -> None:
        result = _discover_target_tests("")
        self.assertIsInstance(result, list)

    def test_returned_list_is_sorted(self) -> None:
        result = _discover_target_tests("framework/worker_runtime.py")
        self.assertEqual(result, sorted(result))


class RunTargetTestsTest(unittest.TestCase):
    def test_empty_list_returns_no_tests_discovered(self) -> None:
        ok, note = _run_target_tests([])
        self.assertTrue(ok)
        self.assertEqual(note, "no_tests_discovered")

    def test_known_passing_test_returns_true(self) -> None:
        test_file = str(TESTS_DIR / "test_stage3_manager_post_apply_validation.py")
        ok, note = _run_target_tests([test_file])
        self.assertTrue(ok, f"expected pass, got note={note!r}")

    def test_passing_note_starts_with_tests_passed(self) -> None:
        test_file = str(TESTS_DIR / "test_stage3_manager_post_apply_validation.py")
        ok, note = _run_target_tests([test_file])
        self.assertTrue(ok)
        self.assertTrue(note.startswith("tests_passed:"), note)

    def test_nonexistent_test_file_returns_false_no_raise(self) -> None:
        ok, note = _run_target_tests(["/nonexistent/xyzzy_test.py"])
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)
        self.assertFalse(ok)

    def test_bad_input_does_not_raise(self) -> None:
        result = _run_target_tests(["not_a_real_file.py"])
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_return_type_is_bool_str(self) -> None:
        ok, note = _run_target_tests([])
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(note, str)


class SourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._source = (REPO_ROOT / "bin" / "stage3_manager.py").read_text(encoding="utf-8")

    def test_discover_target_tests_in_source(self) -> None:
        self.assertIn("_discover_target_tests", self._source)

    def test_run_target_tests_in_source(self) -> None:
        self.assertIn("_run_target_tests", self._source)

    def test_target_test_status_in_source(self) -> None:
        self.assertIn("target_test_status", self._source)

    def test_target_test_note_in_source(self) -> None:
        self.assertIn("target_test_note", self._source)

    def test_reverted_test_failure_in_source(self) -> None:
        self.assertIn("reverted_test_failure", self._source)


class ReferenceBasedDiscoveryTest(unittest.TestCase):
    def test_reference_scan_fires_when_convention_finds_nothing(self) -> None:
        import tempfile
        stem = "xyzzy_synthetic_stem_abc123"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ref_file = td_path / "test_other_module.py"
            ref_file.write_text(f"# references {stem} somewhere\nx = '{stem}'\n", encoding="utf-8")
            result = _discover_target_tests(f"framework/{stem}.py", tests_dir=td_path)
        self.assertIn(str(ref_file), result)

    def test_reference_scan_skipped_when_convention_succeeds(self) -> None:
        import tempfile
        stem = "mymodule_abc"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            conv_file = td_path / f"test_{stem}_something.py"
            conv_file.write_text("# convention match\n", encoding="utf-8")
            ref_file = td_path / "test_other_unrelated.py"
            ref_file.write_text(f"# references {stem}\n", encoding="utf-8")
            result = _discover_target_tests(f"framework/{stem}.py", tests_dir=td_path)
        self.assertIn(str(conv_file), result)
        self.assertNotIn(str(ref_file), result)

    def test_reference_scan_returns_empty_when_no_match(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            unrelated = td_path / "test_unrelated.py"
            unrelated.write_text("# nothing relevant here\n", encoding="utf-8")
            result = _discover_target_tests("framework/completely_unique_xyzzy_zz99.py", tests_dir=td_path)
        self.assertEqual(result, [])

    def test_reference_scan_respects_word_boundary(self) -> None:
        import tempfile
        stem = "my_stem"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            extended = td_path / "test_extended.py"
            extended.write_text("# only mentions my_stem_extended\nx = 'my_stem_extended'\n", encoding="utf-8")
            exact = td_path / "test_exact.py"
            exact.write_text(f"# mentions {stem} exactly\nx = '{stem}'\n", encoding="utf-8")
            result = _discover_target_tests(f"framework/{stem}.py", tests_dir=td_path)
        self.assertIn(str(exact), result)
        self.assertNotIn(str(extended), result)

    def test_reference_scan_result_is_sorted(self) -> None:
        import tempfile
        stem = "sortable_stem_xyz"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            for name in ["test_zzz.py", "test_aaa.py", "test_mmm.py"]:
                (td_path / name).write_text(f"# ref {stem}\n", encoding="utf-8")
            result = _discover_target_tests(f"framework/{stem}.py", tests_dir=td_path)
        self.assertEqual(result, sorted(result))

    def test_reference_scan_result_all_strings(self) -> None:
        import tempfile
        stem = "allstring_stem_xyz"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            (td_path / "test_one.py").write_text(f"# {stem}\n", encoding="utf-8")
            result = _discover_target_tests(f"framework/{stem}.py", tests_dir=td_path)
        for item in result:
            self.assertIsInstance(item, str)

    def test_live_permission_engine_finds_coverage(self) -> None:
        result = _discover_target_tests("framework/permission_engine.py")
        self.assertGreater(len(result), 0, f"expected coverage for permission_engine, got {result}")

    def test_live_learning_hooks_finds_coverage(self) -> None:
        result = _discover_target_tests("framework/learning_hooks.py")
        self.assertGreater(len(result), 0, f"expected coverage for learning_hooks, got {result}")


if __name__ == "__main__":
    unittest.main()
