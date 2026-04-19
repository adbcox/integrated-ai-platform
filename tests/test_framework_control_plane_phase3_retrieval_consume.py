"""Tests for _phase2_derive_read_targets and _phase2_retrieval_summary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import (
    _phase2_derive_read_targets,
    _phase2_retrieval_summary,
)


def _search_result(
    *,
    status="executed",
    query="_execute_job",
    match_count=0,
    matches=None,
    truncated=False,
):
    return {
        "tool_name": "search",
        "status": status,
        "structured_payload": {
            "query": query,
            "match_count": match_count,
            "matches": matches if matches is not None else [],
            "matches_truncated_by_limit": truncated,
        },
        "stdout": "",
        "return_code": 0,
        "duration_ms": 1,
        "error": "",
    }


def _repo_map_result(*, status="executed", entry_count=5, truncated=False):
    return {
        "tool_name": "repo_map",
        "status": status,
        "structured_payload": {
            "entry_count": entry_count,
            "entries": [{"path": f"framework/f{i}.py"} for i in range(entry_count)],
            "truncated": truncated,
        },
        "stdout": "",
        "return_code": 0,
        "duration_ms": 2,
        "error": "",
    }


def _match(path, line=1, text=""):
    return {"path": path, "line_number": line, "line_text": text}


class TestDeriveReadTargetsEmpty(unittest.TestCase):
    def test_empty_list_returns_empty(self):
        self.assertEqual(_phase2_derive_read_targets([]), [])

    def test_no_search_results_returns_empty(self):
        results = [_repo_map_result()]
        self.assertEqual(_phase2_derive_read_targets(results), [])

    def test_search_blocked_returns_empty(self):
        results = [_search_result(status="blocked", matches=[_match("framework/x.py")])]
        self.assertEqual(_phase2_derive_read_targets(results), [])

    def test_search_no_matches_returns_empty(self):
        results = [_search_result(matches=[])]
        self.assertEqual(_phase2_derive_read_targets(results), [])


class TestDeriveReadTargets(unittest.TestCase):
    def test_single_match_returns_one_target(self):
        results = [_search_result(matches=[_match("framework/worker_runtime.py", 10)])]
        targets = _phase2_derive_read_targets(results)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]["arguments"]["path"], "framework/worker_runtime.py")

    def test_deduplicates_paths_preserving_order(self):
        matches = [
            _match("framework/worker_runtime.py", 10),
            _match("framework/worker_runtime.py", 20),
            _match("tests/test_x.py", 5),
        ]
        results = [_search_result(matches=matches)]
        targets = _phase2_derive_read_targets(results)
        self.assertEqual(len(targets), 2)
        self.assertEqual(targets[0]["arguments"]["path"], "framework/worker_runtime.py")
        self.assertEqual(targets[1]["arguments"]["path"], "tests/test_x.py")

    def test_max_files_clamps_targets(self):
        matches = [_match(f"framework/f{i}.py", i) for i in range(10)]
        results = [_search_result(matches=matches)]
        targets = _phase2_derive_read_targets(results, max_files=2)
        self.assertEqual(len(targets), 2)

    def test_default_max_files_is_3(self):
        matches = [_match(f"framework/f{i}.py", i) for i in range(10)]
        results = [_search_result(matches=matches)]
        targets = _phase2_derive_read_targets(results)
        self.assertEqual(len(targets), 3)

    def test_result_dict_shape(self):
        results = [_search_result(matches=[_match("framework/x.py")])]
        targets = _phase2_derive_read_targets(results)
        self.assertEqual(len(targets), 1)
        t = targets[0]
        self.assertEqual(set(t.keys()), {"contract_name", "arguments"})
        self.assertEqual(t["contract_name"], "read_file")
        self.assertEqual(set(t["arguments"].keys()), {"path"})

    def test_multiple_search_results_combined(self):
        r1 = _search_result(matches=[_match("a.py", 1), _match("b.py", 2)])
        r2 = _search_result(matches=[_match("b.py", 3), _match("c.py", 4)])
        targets = _phase2_derive_read_targets([r1, r2], max_files=5)
        paths = [t["arguments"]["path"] for t in targets]
        self.assertEqual(paths, ["b.py", "a.py", "c.py"])


class TestRetrievalSummary(unittest.TestCase):
    def test_empty_returns_safe_defaults(self):
        s = _phase2_retrieval_summary([])
        self.assertEqual(s["query"], "")
        self.assertEqual(s["search_match_count"], 0)
        self.assertEqual(s["unique_file_paths"], [])
        self.assertEqual(s["top_match_file"], "")
        self.assertEqual(s["top_match_line"], 0)
        self.assertFalse(s["search_truncated"])
        self.assertEqual(s["repo_map_entry_count"], 0)
        self.assertFalse(s["repo_map_truncated"])
        self.assertEqual(s["read_targets_derived"], 0)

    def test_query_extracted(self):
        results = [_search_result(query="my_query", matches=[])]
        s = _phase2_retrieval_summary(results)
        self.assertEqual(s["query"], "my_query")

    def test_match_count_extracted(self):
        results = [_search_result(match_count=42, matches=[_match("x.py")])]
        s = _phase2_retrieval_summary(results)
        self.assertEqual(s["search_match_count"], 42)

    def test_top_match_fields(self):
        matches = [_match("framework/worker_runtime.py", 365), _match("tests/t.py", 10)]
        results = [_search_result(matches=matches)]
        s = _phase2_retrieval_summary(results)
        self.assertEqual(s["top_match_file"], "framework/worker_runtime.py")
        self.assertEqual(s["top_match_line"], 365)

    def test_unique_file_paths_deduped(self):
        matches = [
            _match("a.py", 1),
            _match("a.py", 2),
            _match("b.py", 3),
            _match("c.py", 4),
            _match("d.py", 5),
        ]
        results = [_search_result(matches=matches)]
        s = _phase2_retrieval_summary(results, max_files=3)
        self.assertEqual(s["unique_file_paths"], ["a.py", "b.py", "c.py"])

    def test_repo_map_entry_count_extracted(self):
        results = [_repo_map_result(entry_count=7)]
        s = _phase2_retrieval_summary(results)
        self.assertEqual(s["repo_map_entry_count"], 7)

    def test_repo_map_truncated_flag(self):
        results = [_repo_map_result(truncated=True)]
        s = _phase2_retrieval_summary(results)
        self.assertTrue(s["repo_map_truncated"])

    def test_read_targets_derived_count(self):
        matches = [_match("a.py"), _match("b.py"), _match("c.py"), _match("d.py")]
        results = [_search_result(matches=matches)]
        s = _phase2_retrieval_summary(results, max_files=3)
        self.assertEqual(s["read_targets_derived"], 3)


if __name__ == "__main__":
    unittest.main()
