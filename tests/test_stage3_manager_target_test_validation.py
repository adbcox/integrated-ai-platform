"""Tests for _discover_target_tests and _run_target_tests in bin/stage3_manager.py."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.stage3_manager import _discover_target_tests, _run_target_tests  # noqa: E402

TESTS_DIR = REPO_ROOT / "tests"


class DiscoverTargetTestsTest(unittest.TestCase):
    def test_no_match_stem_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            files, mode = _discover_target_tests("framework/xyzzy_nonexistent_module.py", tests_dir=Path(td))
        self.assertEqual(files, [])
        self.assertEqual(mode, "none")

    def test_worker_runtime_returns_nonempty(self) -> None:
        files, mode = _discover_target_tests("framework/worker_runtime.py")
        self.assertGreater(len(files), 0)
        self.assertEqual(mode, "naming_convention")

    def test_all_results_are_strings(self) -> None:
        files, mode = _discover_target_tests("framework/worker_runtime.py")
        for item in files:
            self.assertIsInstance(item, str)

    def test_nonexistent_tests_dir_returns_empty_no_raise(self) -> None:
        files, mode = _discover_target_tests(
            "framework/worker_runtime.py",
            tests_dir=Path("/nonexistent/xyzzy"),
        )
        self.assertEqual(files, [])
        self.assertEqual(mode, "none")

    def test_empty_target_does_not_raise_returns_tuple(self) -> None:
        result = _discover_target_tests("")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        files, mode = result
        self.assertIsInstance(files, list)
        self.assertIsInstance(mode, str)

    def test_returned_list_is_sorted(self) -> None:
        files, mode = _discover_target_tests("framework/worker_runtime.py")
        self.assertEqual(files, sorted(files))


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

    def test_target_test_discovery_mode_in_source(self) -> None:
        self.assertIn("target_test_discovery_mode", self._source)

    def test_target_test_files_count_in_source(self) -> None:
        self.assertIn("target_test_files_count", self._source)

    def test_gates_run_in_source(self) -> None:
        self.assertIn("gates_run", self._source)


class ReferenceBasedDiscoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self._tmp), True)

    def test_reference_scan_fires_when_convention_finds_nothing(self) -> None:
        (self._tmp / "test_other_module.py").write_text("import my_special_stem\n")
        files, mode = _discover_target_tests("src/my_special_stem.py", tests_dir=self._tmp)
        self.assertIn(str(self._tmp / "test_other_module.py"), files)
        self.assertEqual(mode, "reference_scan")

    def test_reference_scan_skipped_when_convention_succeeds(self) -> None:
        (self._tmp / "test_my_special_stem.py").write_text("# convention match\n")
        (self._tmp / "test_other.py").write_text("import my_special_stem\n")
        files, mode = _discover_target_tests("src/my_special_stem.py", tests_dir=self._tmp)
        self.assertEqual(files, [str(self._tmp / "test_my_special_stem.py")])
        self.assertEqual(mode, "naming_convention")

    def test_reference_scan_returns_empty_when_no_match(self) -> None:
        (self._tmp / "test_unrelated.py").write_text("# nothing relevant here\n")
        files, mode = _discover_target_tests("src/xyzzy_unique_99.py", tests_dir=self._tmp)
        self.assertEqual(files, [])
        self.assertEqual(mode, "none")

    def test_reference_scan_respects_word_boundary(self) -> None:
        (self._tmp / "test_edge.py").write_text("import my_stem_extended\n")
        files, mode = _discover_target_tests("src/my_stem.py", tests_dir=self._tmp)
        self.assertEqual(files, [])
        self.assertEqual(mode, "none")

    def test_reference_scan_result_is_sorted(self) -> None:
        (self._tmp / "test_b_module.py").write_text("import my_stem\n")
        (self._tmp / "test_a_module.py").write_text("import my_stem\n")
        files, mode = _discover_target_tests("src/my_stem.py", tests_dir=self._tmp)
        self.assertEqual(files, sorted(files))

    def test_reference_scan_result_all_strings(self) -> None:
        (self._tmp / "test_ref.py").write_text("my_unique_stem()\n")
        files, mode = _discover_target_tests("src/my_unique_stem.py", tests_dir=self._tmp)
        for item in files:
            self.assertIsInstance(item, str)

    def test_live_permission_engine_finds_coverage(self) -> None:
        files, mode = _discover_target_tests("framework/permission_engine.py")
        self.assertGreater(len(files), 0)
        self.assertEqual(mode, "reference_scan")

    def test_live_learning_hooks_finds_coverage(self) -> None:
        files, mode = _discover_target_tests("framework/learning_hooks.py")
        self.assertGreater(len(files), 0)
        self.assertEqual(mode, "reference_scan")


if __name__ == "__main__":
    unittest.main()
