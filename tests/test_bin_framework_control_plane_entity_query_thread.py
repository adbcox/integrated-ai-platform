"""Tests for PHASE3-ENTITY-QUERY-THREAD-1: query forwarded to _phase2_derive_read_targets."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.framework_control_plane import (
    _phase2_derive_read_targets,
    _phase2_retrieval_summary,
)


def _search_obs(matches: list[dict], query: str = "WorkerRuntime execution flow") -> dict:
    return {
        "tool_name": "search",
        "status": "executed",
        "structured_payload": {
            "query": query,
            "match_count": len(matches),
            "matches": matches,
        },
        "stdout": "",
        "return_code": 0,
        "duration_ms": 0,
        "error": "",
    }


def _match(path: str, line: int = 1) -> dict:
    return {"path": path, "line_number": line, "line_text": "x"}


def _two_match_obs(path1: str, path2: str, query: str = "WorkerRuntime execution flow") -> list[dict]:
    return [_search_obs([_match(path1), _match(path2)], query=query)]


class TestEntityQueryBoostWorkeerRuntime(unittest.TestCase):
    """WorkerRuntime query must select worker_runtime.py over aider_micro.sh."""

    def test_worker_runtime_outranks_aider_micro_with_entity_query(self):
        typed_results = _two_match_obs(
            "framework/worker_runtime.py",
            "bin/aider_micro.sh",
            query="WorkerRuntime execution flow",
        )
        targets = _phase2_derive_read_targets(typed_results, query="WorkerRuntime execution flow")
        self.assertGreater(len(targets), 0)
        self.assertIn("worker_runtime", targets[0]["arguments"]["path"])

    def test_worker_runtime_outranks_aider_micro_full_query(self):
        typed_results = _two_match_obs(
            "framework/worker_runtime.py",
            "bin/aider_micro.sh",
            query="WorkerRuntime execution flow and where job execution should be hardened",
        )
        targets = _phase2_derive_read_targets(
            typed_results,
            query="WorkerRuntime execution flow and where job execution should be hardened",
        )
        self.assertIn("worker_runtime", targets[0]["arguments"]["path"])


class TestEmptyQueryNoException(unittest.TestCase):
    def test_empty_query_returns_nonempty_list(self):
        typed_results = _two_match_obs("framework/worker_runtime.py", "bin/aider_micro.sh", query="")
        result = _phase2_derive_read_targets(typed_results, query="")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_empty_query_no_exception(self):
        typed_results = _two_match_obs("framework/worker_runtime.py", "bin/aider_micro.sh")
        try:
            _phase2_derive_read_targets(typed_results, query="")
        except Exception as e:
            self.fail(f"raised: {e}")


class TestQueryChangesRanking(unittest.TestCase):
    def test_entity_query_differs_from_no_query(self):
        typed_results = _two_match_obs(
            "framework/worker_runtime.py",
            "bin/aider_micro.sh",
            query="WorkerRuntime execution flow",
        )
        with_query = _phase2_derive_read_targets(typed_results, query="WorkerRuntime execution flow")
        without_query = _phase2_derive_read_targets(typed_results, query="")
        paths_with = [t["arguments"]["path"] for t in with_query]
        paths_without = [t["arguments"]["path"] for t in without_query]
        self.assertNotEqual(paths_with, paths_without)

    def test_entity_query_top_is_worker_runtime(self):
        typed_results = _two_match_obs(
            "framework/worker_runtime.py",
            "bin/aider_micro.sh",
            query="WorkerRuntime execution flow",
        )
        with_query = _phase2_derive_read_targets(typed_results, query="WorkerRuntime execution flow")
        self.assertIn("worker_runtime", with_query[0]["arguments"]["path"])

    def test_no_query_top_may_be_aider(self):
        typed_results = _two_match_obs(
            "bin/aider_micro.sh",
            "framework/worker_runtime.py",
            query="",
        )
        without_query = _phase2_derive_read_targets(typed_results, query="")
        paths = [t["arguments"]["path"] for t in without_query]
        self.assertTrue(any("aider_micro" in p or "worker_runtime" in p for p in paths))


class TestBinEntrypointOrderingSimulation(unittest.TestCase):
    """Simulate the reordered bin/framework_control_plane.py main() block."""

    def _typed_results(self) -> list[dict]:
        return _two_match_obs(
            "framework/worker_runtime.py",
            "bin/aider_micro.sh",
            query="WorkerRuntime execution flow",
        )

    def test_summary_then_targets_selects_entity_boosted_path(self):
        typed_results = self._typed_results()
        # Step 1: compute summary (extracts query)
        summary = _phase2_retrieval_summary(typed_results)
        extracted_query = str((summary or {}).get("query") or "")
        # Step 2: pass extracted query to derive_read_targets
        targets = _phase2_derive_read_targets(typed_results, query=extracted_query)
        self.assertIn("worker_runtime", targets[0]["arguments"]["path"])

    def test_summary_query_is_nonempty_for_search_obs(self):
        typed_results = self._typed_results()
        summary = _phase2_retrieval_summary(typed_results)
        query = str((summary or {}).get("query") or "")
        self.assertTrue(query, "Expected non-empty query extracted from retrieval summary")

    def test_summary_query_contains_workerruntime(self):
        typed_results = self._typed_results()
        summary = _phase2_retrieval_summary(typed_results)
        query = str((summary or {}).get("query") or "")
        self.assertIn("WorkerRuntime", query)


class TestSourceOrderingAssertion(unittest.TestCase):
    def _src(self) -> str:
        return (REPO_ROOT / "bin" / "framework_control_plane.py").read_text()

    def test_retrieval_summary_before_read_targets_in_source(self):
        src = self._src()
        idx_summary = src.find('"phase2_retrieval_summary"')
        idx_targets = src.find('"phase2_retrieval_read_targets"')
        self.assertGreater(idx_summary, 0)
        self.assertGreater(idx_targets, 0)
        self.assertLess(idx_summary, idx_targets,
                        "phase2_retrieval_summary must be assigned before phase2_retrieval_read_targets")

    def test_derive_read_targets_call_has_query_kwarg(self):
        src = self._src()
        idx = src.find("_phase2_derive_read_targets(")
        block = src[idx: idx + 200]
        self.assertIn("query=", block)


if __name__ == "__main__":
    unittest.main()
