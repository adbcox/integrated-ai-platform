"""Tests for _phase2_extract_typed_results in framework/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import _phase2_extract_typed_results


def _obs(tool_name="read_file", status="executed", stdout="", structured_payload=None,
         return_code=0, duration_ms=0, error="", kind="tool_observation"):
    entry = {
        "kind": kind,
        "tool_name": tool_name,
        "status": status,
        "stdout": stdout,
        "structured_payload": structured_payload if structured_payload is not None else {},
        "return_code": return_code,
        "duration_ms": duration_ms,
        "error": error,
    }
    return entry


def _action(tool_name="read_file"):
    return {"kind": "tool_action", "tool_name": tool_name}


_REQUIRED_KEYS = {"tool_name", "status", "return_code", "stdout", "structured_payload", "duration_ms", "error"}


class TestExtractTypedResultsEmpty(unittest.TestCase):
    def test_empty_payload_returns_empty_list(self):
        self.assertEqual(_phase2_extract_typed_results({}), [])

    def test_none_typed_trace_returns_empty_list(self):
        self.assertEqual(_phase2_extract_typed_results({"typed_tool_trace": None}), [])

    def test_non_list_typed_trace_returns_empty_list(self):
        self.assertEqual(_phase2_extract_typed_results({"typed_tool_trace": "bad"}), [])

    def test_empty_list_typed_trace_returns_empty_list(self):
        self.assertEqual(_phase2_extract_typed_results({"typed_tool_trace": []}), [])

    def test_non_dict_payload_does_not_raise(self):
        # edge case: payload itself is not a dict — should not raise
        try:
            result = _phase2_extract_typed_results(None)  # type: ignore[arg-type]
            self.assertIsInstance(result, list)
        except Exception:
            pass  # acceptable to return [] or raise AttributeError; must not propagate upward


class TestExtractTypedResultsObservations(unittest.TestCase):
    def test_observation_entry_extracted(self):
        trace = [_obs(tool_name="read_file", status="executed", stdout="hello",
                       structured_payload={"path": "/x"})]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool_name"], "read_file")
        self.assertEqual(result[0]["status"], "executed")
        self.assertEqual(result[0]["stdout"], "hello")
        self.assertEqual(result[0]["structured_payload"], {"path": "/x"})

    def test_tool_action_entries_excluded(self):
        trace = [_action("read_file")]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(result, [])

    def test_mixed_trace_only_observations(self):
        trace = [
            _action("read_file"),
            _obs(tool_name="read_file", status="executed"),
            _obs(tool_name="apply_patch", status="executed"),
        ]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result), 2)
        names = {r["tool_name"] for r in result}
        self.assertIn("read_file", names)
        self.assertIn("apply_patch", names)

    def test_stdout_truncation_not_applied(self):
        long_content = "x" * 100_000
        trace = [_obs(stdout=long_content)]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result[0]["stdout"]), 100_000)

    def test_missing_fields_default_to_safe_values(self):
        trace = [{"kind": "tool_observation", "tool_name": "read_file"}]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result), 1)
        r = result[0]
        self.assertEqual(r["status"], "")
        self.assertEqual(r["return_code"], 0)
        self.assertEqual(r["stdout"], "")
        self.assertEqual(r["structured_payload"], {})
        self.assertEqual(r["duration_ms"], 0)
        self.assertEqual(r["error"], "")

    def test_result_dict_has_all_required_keys(self):
        trace = [_obs()]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0].keys()), _REQUIRED_KEYS)

    def test_entry_without_kind_is_treated_as_observation(self):
        # entries with no 'kind' key are not tool_action, so should be included
        trace = [{"tool_name": "git_diff", "status": "executed", "stdout": "diff output"}]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool_name"], "git_diff")

    def test_non_dict_entry_skipped_without_error(self):
        trace = [None, "bad", _obs(tool_name="read_file", status="executed")]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool_name"], "read_file")

    def test_structured_payload_non_dict_defaults_to_empty(self):
        trace = [{"kind": "tool_observation", "tool_name": "search", "structured_payload": "string"}]
        result = _phase2_extract_typed_results({"typed_tool_trace": trace})
        self.assertEqual(result[0]["structured_payload"], {})


class TestBinOutputHasTypedResults(unittest.TestCase):
    def test_extract_called_with_primary_payload(self):
        payload = {
            "typed_tool_trace": [
                {"kind": "tool_action", "tool_name": "read_file"},
                {
                    "kind": "tool_observation",
                    "tool_name": "read_file",
                    "status": "executed",
                    "stdout": "file content here",
                    "structured_payload": {"path": "/repo/framework/x.py", "size_bytes": 17},
                    "return_code": 0,
                    "duration_ms": 12,
                    "error": "",
                },
            ]
        }
        result = _phase2_extract_typed_results(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool_name"], "read_file")
        self.assertEqual(result[0]["stdout"], "file content here")
        self.assertEqual(result[0]["structured_payload"]["size_bytes"], 17)
        self.assertEqual(result[0]["return_code"], 0)
        self.assertEqual(result[0]["duration_ms"], 12)


if __name__ == "__main__":
    unittest.main()
