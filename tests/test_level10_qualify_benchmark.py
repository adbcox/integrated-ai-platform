"""Tests for qualify-v4 benchmark and attribution summarizers in level10_qualify."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))


class SummarizeBenchmarkEmptyTest(unittest.TestCase):
    def _call(self, payload: dict) -> dict:
        from bin.level10_qualify import summarize_benchmark
        return summarize_benchmark(payload)

    def test_empty_dict_returns_zero_structure(self) -> None:
        result = self._call({})
        self.assertEqual(result["class_count"], 0)
        self.assertEqual(result["classes"], {})
        self.assertEqual(result["passed_classes"], [])
        self.assertEqual(result["failed_classes"], [])
        self.assertFalse(result["all_classes_passed"])

    def test_no_classes_key_returns_zero_structure(self) -> None:
        result = self._call({"something_else": 1})
        self.assertEqual(result["class_count"], 0)
        self.assertFalse(result["all_classes_passed"])

    def test_return_type_has_all_required_keys(self) -> None:
        result = self._call({})
        for key in ("class_count", "classes", "passed_classes", "failed_classes", "all_classes_passed"):
            self.assertIn(key, result)


class SummarizeBenchmarkSinglePassingTest(unittest.TestCase):
    def _call(self, payload: dict) -> dict:
        from bin.level10_qualify import summarize_benchmark
        return summarize_benchmark(payload)

    def test_single_passing_class(self) -> None:
        result = self._call({"classes": {"guard_clause": {"passed": True}}})
        self.assertEqual(result["class_count"], 1)
        self.assertEqual(result["classes"], {"guard_clause": True})
        self.assertIn("guard_clause", result["passed_classes"])
        self.assertEqual(result["failed_classes"], [])
        self.assertTrue(result["all_classes_passed"])

    def test_single_failing_class(self) -> None:
        result = self._call({"classes": {"guard_clause": {"passed": False}}})
        self.assertEqual(result["class_count"], 1)
        self.assertIn("guard_clause", result["failed_classes"])
        self.assertEqual(result["passed_classes"], [])
        self.assertFalse(result["all_classes_passed"])


class SummarizeBenchmarkMixedTest(unittest.TestCase):
    def _call(self, payload: dict) -> dict:
        from bin.level10_qualify import summarize_benchmark
        return summarize_benchmark(payload)

    def test_mixed_pass_fail_multi_class(self) -> None:
        payload = {
            "classes": {
                "guard_clause": {"passed": True},
                "assertion_add": {"passed": False},
                "single_file_edit": {"passed": True},
            }
        }
        result = self._call(payload)
        self.assertEqual(result["class_count"], 3)
        self.assertFalse(result["all_classes_passed"])
        self.assertIn("guard_clause", result["passed_classes"])
        self.assertIn("single_file_edit", result["passed_classes"])
        self.assertIn("assertion_add", result["failed_classes"])

    def test_all_passing_classes_sets_all_classes_passed(self) -> None:
        payload = {"classes": {"a": {"passed": True}, "b": {"passed": True}}}
        result = self._call(payload)
        self.assertTrue(result["all_classes_passed"])
        self.assertEqual(len(result["failed_classes"]), 0)

    def test_failed_class_list_is_explicit(self) -> None:
        payload = {"classes": {"x": {"passed": True}, "y": {"passed": False}}}
        result = self._call(payload)
        self.assertIn("y", result["failed_classes"])
        self.assertNotIn("x", result["failed_classes"])
        self.assertIn("x", result["passed_classes"])
        self.assertNotIn("y", result["passed_classes"])

    def test_class_count_matches_classes_dict_length(self) -> None:
        payload = {
            "classes": {
                "a": {"passed": True},
                "b": {"passed": False},
                "c": {"passed": True},
            }
        }
        result = self._call(payload)
        self.assertEqual(result["class_count"], 3)
        self.assertEqual(len(result["classes"]), 3)


class SummarizeAttributionEmptyTest(unittest.TestCase):
    def _call(self, payload: dict) -> dict:
        from bin.level10_qualify import summarize_attribution
        return summarize_attribution(payload)

    def test_empty_dict_returns_zeros(self) -> None:
        result = self._call({})
        self.assertEqual(result["orchestration_delta"], 0.0)
        self.assertEqual(result["model_delta"], 0.0)
        self.assertFalse(result["has_attribution"])

    def test_return_type_has_all_required_keys(self) -> None:
        result = self._call({})
        for key in ("orchestration_delta", "model_delta", "has_attribution"):
            self.assertIn(key, result)

    def test_has_attribution_is_false(self) -> None:
        result = self._call({})
        self.assertIs(result["has_attribution"], False)


class SummarizeAttributionValidTest(unittest.TestCase):
    def _call(self, payload: dict) -> dict:
        from bin.level10_qualify import summarize_attribution
        return summarize_attribution(payload)

    def test_valid_payload_returns_floats(self) -> None:
        result = self._call({"orchestration_delta": 0.15, "model_delta": -0.05})
        self.assertAlmostEqual(result["orchestration_delta"], 0.15)
        self.assertAlmostEqual(result["model_delta"], -0.05)

    def test_has_attribution_true_for_non_empty(self) -> None:
        result = self._call({"orchestration_delta": 0.1, "model_delta": 0.0})
        self.assertTrue(result["has_attribution"])

    def test_missing_keys_default_to_zero(self) -> None:
        result = self._call({"some_other_key": "value"})
        self.assertEqual(result["orchestration_delta"], 0.0)
        self.assertEqual(result["model_delta"], 0.0)
        self.assertTrue(result["has_attribution"])

    def test_negative_delta_preserved(self) -> None:
        result = self._call({"orchestration_delta": -0.3, "model_delta": 0.5})
        self.assertAlmostEqual(result["orchestration_delta"], -0.3)


class EvaluateV8GatesBenchmarkAttributionTest(unittest.TestCase):
    def _run(
        self,
        benchmark_stats: dict | None = None,
        attribution_stats: dict | None = None,
        manifest_data: dict | None = None,
    ) -> dict:
        from bin.level10_qualify import evaluate_v8_gates
        return evaluate_v8_gates(
            manifest_data=manifest_data or {},
            stage8_stats={},
            rag6_stats={},
            assessments={},
            gate_chain_stats={},
            benchmark_stats=benchmark_stats,
            attribution_stats=attribution_stats,
        )

    def test_no_stats_both_gates_false(self) -> None:
        result = self._run()
        self.assertFalse(result["gates"]["benchmark8_ready"])
        self.assertFalse(result["gates"]["attribution8_ready"])

    def test_passing_benchmark_one_class_ready(self) -> None:
        from bin.level10_qualify import summarize_benchmark
        bench = summarize_benchmark({"classes": {"guard_clause": {"passed": True}}})
        result = self._run(benchmark_stats=bench)
        self.assertTrue(result["gates"]["benchmark8_ready"])

    def test_insufficient_class_count_not_ready(self) -> None:
        from bin.level10_qualify import summarize_benchmark
        bench = summarize_benchmark({"classes": {"guard_clause": {"passed": True}}})
        manifest = {"promotion_policy": {"criteria": {"benchmark_min_class_count": 2}}}
        result = self._run(benchmark_stats=bench, manifest_data=manifest)
        self.assertFalse(result["gates"]["benchmark8_ready"])

    def test_benchmark_class_present_but_failed_not_ready(self) -> None:
        from bin.level10_qualify import summarize_benchmark
        bench = summarize_benchmark({"classes": {"guard_clause": {"passed": False}}})
        result = self._run(benchmark_stats=bench)
        self.assertFalse(result["gates"]["benchmark8_ready"])

    def test_attribution_payload_present_ready(self) -> None:
        from bin.level10_qualify import summarize_attribution
        attr = summarize_attribution({"orchestration_delta": 0.1, "model_delta": 0.0})
        result = self._run(attribution_stats=attr)
        self.assertTrue(result["gates"]["attribution8_ready"])

    def test_both_gates_in_gates_dict(self) -> None:
        result = self._run()
        self.assertIn("benchmark8_ready", result["gates"])
        self.assertIn("attribution8_ready", result["gates"])

    def test_missing_list_includes_new_gates_when_false(self) -> None:
        result = self._run()
        self.assertIn("benchmark8_ready", result["missing"])
        self.assertIn("attribution8_ready", result["missing"])

    def test_existing_callers_without_new_kwargs_still_work(self) -> None:
        from bin.level10_qualify import evaluate_v8_gates
        result = evaluate_v8_gates(
            manifest_data={},
            stage8_stats={},
            rag6_stats={},
            assessments={},
            gate_chain_stats={},
        )
        self.assertIn("benchmark8_ready", result["gates"])
        self.assertIn("attribution8_ready", result["gates"])
        self.assertFalse(result["gates"]["benchmark8_ready"])
        self.assertFalse(result["gates"]["attribution8_ready"])


class SourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "level10_qualify.py").read_text(encoding="utf-8")

    def test_default_benchmark_constant_present(self) -> None:
        self.assertIn("DEFAULT_CODEX51_BENCHMARK_LATEST", self._src)

    def test_default_attribution_constant_present(self) -> None:
        self.assertIn("DEFAULT_CODEX51_ATTRIBUTION_LATEST", self._src)

    def test_summarize_benchmark_defined(self) -> None:
        self.assertIn("def summarize_benchmark", self._src)

    def test_summarize_attribution_defined(self) -> None:
        self.assertIn("def summarize_attribution", self._src)

    def test_benchmark8_ready_gate_present(self) -> None:
        self.assertIn("benchmark8_ready", self._src)

    def test_attribution8_ready_gate_present(self) -> None:
        self.assertIn("attribution8_ready", self._src)

    def test_benchmark_min_class_count_criterion_read(self) -> None:
        self.assertIn("benchmark_min_class_count", self._src)

    def test_all_classes_passed_field_used(self) -> None:
        self.assertIn("all_classes_passed", self._src)

    def test_has_attribution_field_used(self) -> None:
        self.assertIn("has_attribution", self._src)


if __name__ == "__main__":
    unittest.main()
