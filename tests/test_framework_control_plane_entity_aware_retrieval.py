"""Tests for entity-aware retrieval boosting in framework/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.framework_control_plane import (
    _extract_phase3_entities,
    _phase2_derive_read_targets,
    _phase2_retrieval_summary,
)


def _search_entry(matches: list[dict]) -> dict:
    return {
        "tool_name": "search",
        "status": "executed",
        "structured_payload": {
            "query": "test",
            "match_count": len(matches),
            "matches": matches,
        },
    }


def _match(path: str, line: int = 1) -> dict:
    return {"path": path, "line_number": line, "context": ""}


class TestExtractPhase3Entities(unittest.TestCase):
    def test_camelcase_detected(self):
        entities = _extract_phase3_entities("WorkerRuntime execution flow")
        self.assertIn("WorkerRuntime", entities)

    def test_plain_words_excluded(self):
        entities = _extract_phase3_entities("execution flow job hardened")
        self.assertEqual(entities, set())

    def test_multiple_camelcase(self):
        entities = _extract_phase3_entities("ExecutorFactory and WorkerRuntime")
        self.assertIn("ExecutorFactory", entities)
        self.assertIn("WorkerRuntime", entities)

    def test_allcaps_detected(self):
        entities = _extract_phase3_entities("RAG pipeline")
        self.assertIn("RAG", entities)

    def test_short_allcaps_excluded(self):
        entities = _extract_phase3_entities("AI is great")
        self.assertNotIn("AI", entities)

    def test_empty_query_returns_empty(self):
        self.assertEqual(_extract_phase3_entities(""), set())

    def test_none_returns_empty(self):
        self.assertEqual(_extract_phase3_entities(None), set())  # type: ignore[arg-type]

    def test_in_all(self):
        import framework.framework_control_plane as m
        self.assertIn("_extract_phase3_entities", m.__all__)

    def test_punctuation_stripped(self):
        entities = _extract_phase3_entities("(WorkerRuntime)")
        self.assertIn("WorkerRuntime", entities)


class TestDeriveReadTargetsEntityBoost(unittest.TestCase):
    """WorkerRuntime query must prefer framework/worker_runtime.py over bin/aider_micro.sh."""

    def _make_results(self, paths: list[str]) -> list[dict]:
        matches = [_match(p) for p in paths]
        return [_search_entry(matches)]

    def test_workerruntime_query_prefers_worker_runtime_py(self):
        paths = ["framework/worker_runtime.py", "bin/aider_micro.sh"]
        results = self._make_results(paths)
        targets = _phase2_derive_read_targets(results, max_files=1, query="WorkerRuntime execution flow job hardened")
        self.assertEqual(len(targets), 1)
        self.assertIn("worker_runtime", targets[0]["arguments"]["path"])

    def test_codeexecutor_query_prefers_code_executor_py(self):
        # 'CodeExecutor' normalizes to 'codeexecutor' == stem of code_executor.py
        paths = ["framework/code_executor.py", "bin/aider_micro.sh"]
        results = self._make_results(paths)
        targets = _phase2_derive_read_targets(results, max_files=1, query="CodeExecutor improve dispatch")
        self.assertIn("code_executor", targets[0]["arguments"]["path"])

    def test_entity_stem_exact_match_beats_alphabetical_tie(self):
        # Both paths have same base frequency; entity match should win
        paths = ["framework/worker_runtime.py", "framework/aaa_other.py"]
        results = self._make_results(paths)
        targets = _phase2_derive_read_targets(results, max_files=1, query="WorkerRuntime refactor")
        self.assertIn("worker_runtime", targets[0]["arguments"]["path"])

    def test_no_query_keeps_original_scoring(self):
        paths = ["framework/worker_runtime.py", "bin/aider_micro.sh"]
        results = self._make_results(paths)
        # Without query, framework/ dir bonus still wins over bin/
        targets = _phase2_derive_read_targets(results, max_files=2)
        self.assertEqual(len(targets), 2)

    def test_entity_boost_does_not_raise_on_empty_query(self):
        paths = ["framework/worker_runtime.py"]
        results = self._make_results(paths)
        try:
            _phase2_derive_read_targets(results, max_files=1, query="")
        except Exception as e:
            self.fail(f"Raised: {e}")

    def test_entity_boost_does_not_raise_on_none_query(self):
        paths = ["framework/worker_runtime.py"]
        results = self._make_results(paths)
        try:
            _phase2_derive_read_targets(results, max_files=1, query=None)  # type: ignore[arg-type]
        except Exception as e:
            self.fail(f"Raised: {e}")


class TestRetrievalSummaryEntityBoost(unittest.TestCase):
    """_phase2_retrieval_summary must propagate entity boost to its ranked paths."""

    def _make_results(self, paths: list[str], query: str = "test") -> list[dict]:
        matches = [_match(p) for p in paths]
        return [
            {
                "tool_name": "search",
                "status": "executed",
                "structured_payload": {
                    "query": query,
                    "match_count": len(matches),
                    "matches": matches,
                },
            }
        ]

    def test_workerruntime_query_top_file_is_worker_runtime(self):
        paths = ["framework/worker_runtime.py", "bin/aider_micro.sh"]
        results = self._make_results(paths, query="WorkerRuntime execution flow")
        summary = _phase2_retrieval_summary(results, max_files=2)
        self.assertIn("worker_runtime", summary["top_match_file"])

    def test_summary_unique_file_paths_includes_worker_runtime_first(self):
        paths = ["framework/worker_runtime.py", "bin/aider_micro.sh"]
        results = self._make_results(paths, query="WorkerRuntime execution flow")
        summary = _phase2_retrieval_summary(results, max_files=2)
        self.assertTrue(summary["unique_file_paths"][0].endswith("worker_runtime.py"))

    def test_no_entity_query_still_returns_summary_dict(self):
        paths = ["framework/worker_runtime.py"]
        results = self._make_results(paths, query="generic query words only")
        summary = _phase2_retrieval_summary(results, max_files=1)
        self.assertIsInstance(summary, dict)
        self.assertIn("top_match_file", summary)


if __name__ == "__main__":
    unittest.main()
