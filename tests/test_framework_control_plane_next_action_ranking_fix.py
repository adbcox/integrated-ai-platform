"""Tests for PHASE3-NEXT-ACTION-RANKING-FIX-1: next_action content-char gate and retrieval ranking penalties."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.framework_control_plane import (
    _DERIVE_TARGETS_LOW_VALUE_DIRS,
    _SAFE_NEXT_ACTION,
    _phase2_derive_read_targets,
    _phase2_retrieval_summary,
    _phase3_derive_next_action,
)


def _bundle(
    prompt_ready: bool = True,
    total_files: int = 1,
    total_symbols: int = 0,
    total_content_chars: int = 0,
    query: str = "test query",
) -> dict:
    return {
        "query": query,
        "prompt_ready": prompt_ready,
        "total_files": total_files,
        "total_symbols": total_symbols,
        "total_content_chars": total_content_chars,
        "files_with_symbols": 0,
        "files": [],
        "top_file": "",
        "top_file_symbol_count": 0,
    }


def _inf(has_content: bool = True, output: str = "some content") -> dict:
    return {"has_content": has_content, "output": output, "metadata": {}}


def _search_obs(matches: list[dict], query: str = "test") -> dict:
    return {
        "tool_name": "search",
        "status": "executed",
        "structured_payload": {"query": query, "match_count": len(matches), "matches": matches},
        "stdout": "",
        "return_code": 0,
        "duration_ms": 0,
        "error": "",
    }


def _match(path: str, line: int = 1) -> dict:
    return {"path": path, "line_number": line, "line_text": "x"}


class TestNextActionContentCharsGate(unittest.TestCase):
    def test_refine_retrieval_when_symbols_zero_and_chars_zero(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=0, total_content_chars=0), _inf())
        self.assertEqual(result["action"], "refine_retrieval")

    def test_ready_when_symbols_zero_and_chars_500(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=0, total_content_chars=500), _inf())
        self.assertEqual(result["action"], "ready")

    def test_refine_retrieval_when_symbols_zero_and_chars_100(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=0, total_content_chars=100), _inf())
        self.assertEqual(result["action"], "refine_retrieval")

    def test_refine_retrieval_when_symbols_zero_and_chars_199(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=0, total_content_chars=199), _inf())
        self.assertEqual(result["action"], "refine_retrieval")

    def test_ready_when_symbols_zero_and_chars_201(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=0, total_content_chars=201), _inf())
        self.assertEqual(result["action"], "ready")

    def test_ready_when_symbols_positive_and_chars_zero(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=5, total_content_chars=0), _inf())
        self.assertEqual(result["action"], "ready")

    def test_no_context_when_prompt_ready_false_regardless_of_chars(self):
        result = _phase3_derive_next_action(_bundle(prompt_ready=False, total_content_chars=999), _inf())
        self.assertEqual(result["action"], "no_context")

    def test_insufficient_context_when_inference_has_no_content(self):
        result = _phase3_derive_next_action(_bundle(total_content_chars=500), _inf(has_content=False))
        self.assertEqual(result["action"], "insufficient_context")

    def test_returned_dict_contains_total_content_chars(self):
        result = _phase3_derive_next_action(_bundle(total_content_chars=300), _inf())
        self.assertIn("total_content_chars", result)

    def test_returned_total_content_chars_matches_bundle_value(self):
        result = _phase3_derive_next_action(_bundle(total_content_chars=42), _inf())
        self.assertEqual(result["total_content_chars"], 42)

    def test_safe_next_action_has_total_content_chars(self):
        self.assertIn("total_content_chars", _SAFE_NEXT_ACTION)
        self.assertEqual(_SAFE_NEXT_ACTION["total_content_chars"], 0)

    def test_refine_retrieval_reason_contains_chars_when_content_triggered(self):
        result = _phase3_derive_next_action(_bundle(total_symbols=0, total_content_chars=50), _inf())
        self.assertIn("chars=", result["reason"])

    def test_no_exception_when_bundle_missing_total_content_chars(self):
        b = _bundle()
        del b["total_content_chars"]
        try:
            _phase3_derive_next_action(b, _inf())
        except Exception as e:
            self.fail(f"raised: {e}")


class TestRetrievalRankingPenalties(unittest.TestCase):
    def _single_match_obs(self, path: str) -> list[dict]:
        return [_search_obs([_match(path)])]

    def _two_match_obs(self, path1: str, path2: str) -> list[dict]:
        return [_search_obs([_match(path1), _match(path2)])]

    def test_framework_worker_runtime_outranks_claude_md(self):
        obs = self._two_match_obs("framework/worker_runtime.py", "CLAUDE.md")
        result = _phase2_derive_read_targets(obs, max_files=1)
        self.assertEqual(len(result), 1)
        self.assertIn("worker_runtime", result[0]["arguments"]["path"])

    def test_governance_json_outranked_by_bin_stage3(self):
        obs = self._two_match_obs("governance/schema.json", "bin/stage3_manager.py")
        result = _phase2_derive_read_targets(obs, max_files=1)
        self.assertIn("stage3", result[0]["arguments"]["path"])

    def test_config_json_outranked_by_framework_executor(self):
        obs = self._two_match_obs("config/promotion_manifest.json", "framework/code_executor.py")
        result = _phase2_derive_read_targets(obs, max_files=1)
        self.assertIn("code_executor", result[0]["arguments"]["path"])

    def test_docs_md_outranked_by_tests_file(self):
        obs = self._two_match_obs("docs/roadmap.md", "tests/test_worker.py")
        result = _phase2_derive_read_targets(obs, max_files=1)
        self.assertIn("test_worker", result[0]["arguments"]["path"])

    def test_framework_json_not_penalized_by_non_source_json_rule(self):
        obs = self._two_match_obs("framework/something.json", "config/settings.json")
        result = _phase2_derive_read_targets(obs, max_files=1)
        self.assertIn("framework", result[0]["arguments"]["path"])

    def test_derive_targets_low_value_dirs_contents(self):
        self.assertIn("governance", _DERIVE_TARGETS_LOW_VALUE_DIRS)
        self.assertIn("config", _DERIVE_TARGETS_LOW_VALUE_DIRS)
        self.assertIn("docs", _DERIVE_TARGETS_LOW_VALUE_DIRS)
        self.assertIn("artifacts", _DERIVE_TARGETS_LOW_VALUE_DIRS)

    def test_init_py_penalty_still_effective(self):
        obs = self._two_match_obs("__init__.py", "framework/worker_runtime.py")
        result = _phase2_derive_read_targets(obs, max_files=1)
        self.assertIn("worker_runtime", result[0]["arguments"]["path"])

    def test_no_exception_on_empty_typed_results(self):
        try:
            _phase2_derive_read_targets([])
        except Exception as e:
            self.fail(f"raised: {e}")

    def test_retrieval_summary_top_match_prefers_framework_over_config(self):
        obs = [_search_obs([_match("config/settings.json"), _match("framework/worker_runtime.py")])]
        summary = _phase2_retrieval_summary(obs)
        self.assertIn("framework", summary["top_match_file"])


class TestSourceTextAssertions(unittest.TestCase):
    def _src(self) -> str:
        return (REPO_ROOT / "framework" / "framework_control_plane.py").read_text()

    def test_derive_targets_low_value_dirs_in_source(self):
        self.assertIn("_DERIVE_TARGETS_LOW_VALUE_DIRS", self._src())

    def test_total_content_chars_le_200_condition_in_source(self):
        self.assertIn("total_content_chars <= 200", self._src())

    def test_total_content_chars_in_safe_next_action(self):
        src = self._src()
        idx = src.find("_SAFE_NEXT_ACTION")
        block = src[idx:idx + 300]
        self.assertIn("total_content_chars", block)


if __name__ == "__main__":
    unittest.main()
