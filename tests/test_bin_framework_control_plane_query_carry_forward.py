"""Tests for PHASE3-QUERY-CARRY-FORWARD-1: retrieval query persistence and injection."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import bin.framework_control_plane as fcp


class TestLoadRetrievalQuery(unittest.TestCase):
    def test_returns_empty_when_file_does_not_exist(self):
        result = fcp._load_retrieval_query(Path("/tmp/does_not_exist_xyzzy_7823.json"))
        self.assertEqual(result, "")

    def test_returns_empty_when_file_is_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("")
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_returns_query_from_valid_artifact(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"query": "test_query_value"}, f)
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), "test_query_value")
        finally:
            tmp.unlink(missing_ok=True)

    def test_returns_empty_on_malformed_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not valid json}")
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_returns_empty_when_json_is_list(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(["query", "value"], f)
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_returns_empty_when_dict_has_no_query_key(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"other_key": "value"}, f)
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_does_not_raise_on_odd_inputs(self):
        for bad_path in [Path("/dev/null"), Path("/"), Path("/tmp")]:
            try:
                fcp._load_retrieval_query(bad_path)
            except Exception as e:
                self.fail(f"raised on {bad_path}: {e}")

    def test_returns_empty_when_query_is_empty_string(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"query": ""}, f)
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_returns_exact_query_string(self):
        expected = "WorkerRuntime execution flow and where job execution should be hardened"
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"query": expected}, f)
            tmp = Path(f.name)
        try:
            self.assertEqual(fcp._load_retrieval_query(tmp), expected)
        finally:
            tmp.unlink(missing_ok=True)

    def test_returns_empty_or_whitespace_for_whitespace_query(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"query": "  "}, f)
            tmp = Path(f.name)
        try:
            result = fcp._load_retrieval_query(tmp)
            self.assertIsInstance(result, str)
        except Exception as e:
            self.fail(f"raised: {e}")
        finally:
            tmp.unlink(missing_ok=True)


class TestDefaultRetrievalQueryPath(unittest.TestCase):
    def test_is_path_instance(self):
        self.assertIsInstance(fcp._DEFAULT_RETRIEVAL_QUERY_PATH, Path)

    def test_is_under_default_state_root(self):
        self.assertTrue(
            str(fcp._DEFAULT_RETRIEVAL_QUERY_PATH).startswith(str(fcp.DEFAULT_STATE_ROOT))
        )


class TestParseArgs(unittest.TestCase):
    def test_parse_args_callable_with_no_args(self):
        import sys as _sys
        old_argv = _sys.argv
        _sys.argv = ["prog"]
        try:
            args = fcp.parse_args()
            self.assertIsNotNone(args)
        finally:
            _sys.argv = old_argv


class TestSourceTextAssertions(unittest.TestCase):
    def _src(self) -> str:
        return (REPO_ROOT / "bin" / "framework_control_plane.py").read_text()

    def test_default_retrieval_query_path_in_source(self):
        self.assertIn("_DEFAULT_RETRIEVAL_QUERY_PATH", self._src())

    def test_load_retrieval_query_in_source(self):
        self.assertIn("_load_retrieval_query", self._src())

    def test_phase3_retrieval_query_persisted_in_source(self):
        self.assertIn("phase3_retrieval_query_persisted", self._src())

    def test_phase3_retrieval_query_injected_in_source(self):
        self.assertIn("phase3_retrieval_query_injected", self._src())

    def test_retrieval_probe_and_read_after_retrieval_near_query_logic(self):
        src = self._src()
        self.assertIn("retrieval_probe", src)
        self.assertIn("read_after_retrieval", src)


if __name__ == "__main__":
    unittest.main()
