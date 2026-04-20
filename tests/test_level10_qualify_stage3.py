"""Tests for summarize_gate_chain in bin/level10_qualify.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.level10_qualify import summarize_gate_chain  # noqa: E402

_FULL = {
    "accepted": True,
    "gates_run": ["g1_syntax", "g2_tests", "g3_repo_check", "g4_repo_quick"],
    "target_test_discovery_mode": "naming_convention",
    "classification": "accepted",
}
_SMOKE = {
    "accepted": True,
    "gates_run": ["g1_syntax", "g2_tests", "g3_repo_check", "g4_repo_quick"],
    "target_test_discovery_mode": "none",
    "classification": "accepted",
}
_PARTIAL = {
    "accepted": True,
    "gates_run": ["g1_syntax"],
    "target_test_discovery_mode": "skipped",
    "classification": "accepted",
}
_REJECTED = {
    "accepted": False,
    "gates_run": ["g1_syntax"],
    "target_test_discovery_mode": "skipped",
    "classification": "reverted_test_failure",
}


class SummarizeGateChainEmptyTest(unittest.TestCase):
    def setUp(self) -> None:
        self._result = summarize_gate_chain([])

    def test_total_is_zero(self) -> None:
        self.assertEqual(self._result["total"], 0)

    def test_accepted_is_zero(self) -> None:
        self.assertEqual(self._result["accepted"], 0)

    def test_fully_qualified_is_zero(self) -> None:
        self.assertEqual(self._result["fully_qualified"], 0)

    def test_qualification_rate_is_zero(self) -> None:
        self.assertEqual(self._result["qualification_rate"], 0.0)

    def test_full_qualification_rate_is_zero(self) -> None:
        self.assertEqual(self._result["full_qualification_rate"], 0.0)

    def test_gate_coverage_all_zero(self) -> None:
        gc = self._result["gate_coverage"]
        self.assertEqual(gc["g1_syntax"], 0)
        self.assertEqual(gc["g2_tests"], 0)
        self.assertEqual(gc["g3_repo_check"], 0)
        self.assertEqual(gc["g4_repo_quick"], 0)

    def test_discovery_mode_distribution_empty(self) -> None:
        self.assertEqual(self._result["discovery_mode_distribution"], {})

    def test_classification_distribution_empty(self) -> None:
        self.assertEqual(self._result["classification_distribution"], {})


class SummarizeGateChainFullyQualifiedTest(unittest.TestCase):
    def setUp(self) -> None:
        self._result = summarize_gate_chain([_FULL])

    def test_total_is_one(self) -> None:
        self.assertEqual(self._result["total"], 1)

    def test_accepted_is_one(self) -> None:
        self.assertEqual(self._result["accepted"], 1)

    def test_rejected_is_zero(self) -> None:
        self.assertEqual(self._result["rejected"], 0)

    def test_fully_qualified_is_one(self) -> None:
        self.assertEqual(self._result["fully_qualified"], 1)

    def test_qualified_smoke_fallback_is_zero(self) -> None:
        self.assertEqual(self._result["qualified_smoke_fallback"], 0)

    def test_qualification_rate_is_one(self) -> None:
        self.assertEqual(self._result["qualification_rate"], 1.0)

    def test_full_qualification_rate_is_one(self) -> None:
        self.assertEqual(self._result["full_qualification_rate"], 1.0)

    def test_all_gates_covered(self) -> None:
        gc = self._result["gate_coverage"]
        self.assertEqual(gc["g1_syntax"], 1)
        self.assertEqual(gc["g2_tests"], 1)
        self.assertEqual(gc["g3_repo_check"], 1)
        self.assertEqual(gc["g4_repo_quick"], 1)

    def test_discovery_mode_distribution_has_naming_convention(self) -> None:
        self.assertIn("naming_convention", self._result["discovery_mode_distribution"])


class SummarizeGateChainSmokeFallbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self._result = summarize_gate_chain([_SMOKE])

    def test_total_is_one(self) -> None:
        self.assertEqual(self._result["total"], 1)

    def test_accepted_is_one(self) -> None:
        self.assertEqual(self._result["accepted"], 1)

    def test_fully_qualified_is_zero(self) -> None:
        self.assertEqual(self._result["fully_qualified"], 0)

    def test_qualified_smoke_fallback_is_one(self) -> None:
        self.assertEqual(self._result["qualified_smoke_fallback"], 1)

    def test_full_qualification_rate_is_zero(self) -> None:
        self.assertEqual(self._result["full_qualification_rate"], 0.0)

    def test_qualification_rate_is_one(self) -> None:
        self.assertEqual(self._result["qualification_rate"], 1.0)


class SummarizeGateChainMixedTest(unittest.TestCase):
    def setUp(self) -> None:
        self._result = summarize_gate_chain([_FULL, _SMOKE, _PARTIAL, _REJECTED])

    def test_total_is_four(self) -> None:
        self.assertEqual(self._result["total"], 4)

    def test_accepted_is_three(self) -> None:
        self.assertEqual(self._result["accepted"], 3)

    def test_rejected_is_one(self) -> None:
        self.assertEqual(self._result["rejected"], 1)

    def test_fully_qualified_is_one(self) -> None:
        self.assertEqual(self._result["fully_qualified"], 1)

    def test_qualified_smoke_fallback_is_one(self) -> None:
        self.assertEqual(self._result["qualified_smoke_fallback"], 1)

    def test_qualified_partial_gates_is_one(self) -> None:
        self.assertEqual(self._result["qualified_partial_gates"], 1)

    def test_qualification_rate(self) -> None:
        self.assertEqual(self._result["qualification_rate"], 0.75)

    def test_full_qualification_rate(self) -> None:
        self.assertEqual(self._result["full_qualification_rate"], 0.25)

    def test_classification_distribution_has_rejected(self) -> None:
        self.assertIn("reverted_test_failure", self._result["classification_distribution"])

    def test_g1_syntax_covers_all_four(self) -> None:
        self.assertEqual(self._result["gate_coverage"]["g1_syntax"], 4)

    def test_g4_repo_quick_covers_two(self) -> None:
        self.assertEqual(self._result["gate_coverage"]["g4_repo_quick"], 2)


class SummarizeGateChainReturnTypeTest(unittest.TestCase):
    def test_return_is_dict(self) -> None:
        result = summarize_gate_chain([])
        self.assertIsInstance(result, dict)

    def test_gate_coverage_is_dict(self) -> None:
        result = summarize_gate_chain([])
        self.assertIsInstance(result["gate_coverage"], dict)

    def test_discovery_mode_distribution_is_dict(self) -> None:
        result = summarize_gate_chain([])
        self.assertIsInstance(result["discovery_mode_distribution"], dict)

    def test_classification_distribution_is_dict(self) -> None:
        result = summarize_gate_chain([])
        self.assertIsInstance(result["classification_distribution"], dict)

    def test_qualification_rate_is_float(self) -> None:
        result = summarize_gate_chain([_FULL])
        self.assertIsInstance(result["qualification_rate"], float)

    def test_full_qualification_rate_is_float(self) -> None:
        result = summarize_gate_chain([_FULL])
        self.assertIsInstance(result["full_qualification_rate"], float)


class SummarizeGateChainSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._source = (REPO_ROOT / "bin" / "level10_qualify.py").read_text(encoding="utf-8")

    def test_summarize_gate_chain_in_source(self) -> None:
        self.assertIn("summarize_gate_chain", self._source)

    def test_default_stage3_trace_in_source(self) -> None:
        self.assertIn("DEFAULT_STAGE3_TRACE", self._source)

    def test_stage3_trace_cli_arg_in_source(self) -> None:
        self.assertIn("--stage3-trace", self._source)

    def test_fully_qualified_in_source(self) -> None:
        self.assertIn("fully_qualified", self._source)

    def test_gate_coverage_in_source(self) -> None:
        self.assertIn("gate_coverage", self._source)

    def test_full_qualification_rate_in_source(self) -> None:
        self.assertIn("full_qualification_rate", self._source)

    def test_gate_chain_key_in_source(self) -> None:
        self.assertIn('"gate_chain"', self._source)

    def test_stage3_rows_in_source(self) -> None:
        self.assertIn("stage3_rows", self._source)


class EvaluateV8GatesGateChainTest(unittest.TestCase):
    """Verify gate_chain_ready participates in evaluate_v8_gates."""

    def _run(self, gate_chain_stats: dict) -> dict:
        from bin.level10_qualify import evaluate_v8_gates
        return evaluate_v8_gates(
            manifest_data={},
            stage8_stats={},
            rag6_stats={},
            assessments={},
            gate_chain_stats=gate_chain_stats,
        )

    def test_empty_gate_chain_gate_chain_ready_false(self) -> None:
        result = self._run({})
        self.assertFalse(result["gates"]["gate_chain_ready"])

    def test_zero_total_gate_chain_ready_false(self) -> None:
        result = self._run({"total": 0, "full_qualification_rate": 1.0,
                            "gate_coverage": {"g4_repo_quick": 1}})
        self.assertFalse(result["gates"]["gate_chain_ready"])

    def test_low_fqr_gate_chain_ready_false(self) -> None:
        result = self._run({"total": 10, "full_qualification_rate": 0.3,
                            "gate_coverage": {"g4_repo_quick": 5}})
        self.assertFalse(result["gates"]["gate_chain_ready"])

    def test_zero_g4_coverage_gate_chain_ready_false(self) -> None:
        result = self._run({"total": 10, "full_qualification_rate": 0.8,
                            "gate_coverage": {"g4_repo_quick": 0}})
        self.assertFalse(result["gates"]["gate_chain_ready"])

    def test_missing_g4_key_gate_chain_ready_false(self) -> None:
        result = self._run({"total": 10, "full_qualification_rate": 0.8,
                            "gate_coverage": {}})
        self.assertFalse(result["gates"]["gate_chain_ready"])

    def test_exactly_threshold_gate_chain_ready_true(self) -> None:
        result = self._run({"total": 10, "full_qualification_rate": 0.5,
                            "gate_coverage": {"g4_repo_quick": 1}})
        self.assertTrue(result["gates"]["gate_chain_ready"])

    def test_above_threshold_gate_chain_ready_true(self) -> None:
        result = self._run({"total": 20, "full_qualification_rate": 0.9,
                            "gate_coverage": {"g4_repo_quick": 18}})
        self.assertTrue(result["gates"]["gate_chain_ready"])

    def test_gate_chain_ready_key_present_in_gates(self) -> None:
        result = self._run({})
        self.assertIn("gate_chain_ready", result["gates"])

    def test_gate_chain_ready_false_appears_in_missing(self) -> None:
        result = self._run({})
        self.assertIn("gate_chain_ready", result["missing"])

    def test_gate_chain_ready_true_absent_from_missing(self) -> None:
        result = self._run({"total": 10, "full_qualification_rate": 0.5,
                            "gate_coverage": {"g4_repo_quick": 1}})
        self.assertNotIn("gate_chain_ready", result["missing"])

    def test_all_ready_false_when_gate_chain_empty(self) -> None:
        result = self._run({})
        self.assertFalse(result["all_ready"])

    def test_return_has_gates_all_ready_missing(self) -> None:
        result = self._run({})
        self.assertIn("gates", result)
        self.assertIn("all_ready", result)
        self.assertIn("missing", result)


class UpdatedSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "level10_qualify.py").read_text(encoding="utf-8")

    def test_gate_chain_ready_in_source(self) -> None:
        self.assertIn("gate_chain_ready", self._src)

    def test_gate_chain_stats_param_in_evaluate_v8_gates(self) -> None:
        self.assertIn("gate_chain_stats", self._src)

    def test_full_qualification_rate_threshold_in_source(self) -> None:
        self.assertIn("0.5", self._src)

    def test_g4_repo_quick_guard_in_source(self) -> None:
        self.assertIn("g4_repo_quick", self._src)


class EvaluateSubsystemsGateChainTest(unittest.TestCase):
    """Verify gate_chain assessment is produced by evaluate_subsystems."""

    def _run(self, gate_chain_stats: dict, threshold: float = 0.5) -> dict:
        from collections import Counter as _Counter
        from bin.level10_qualify import evaluate_subsystems
        return evaluate_subsystems(
            subsystem_levels={},
            candidate_stats=_Counter(),
            stage6_stats=_Counter(),
            worker_stats=_Counter(),
            rag4_stats={"plans": 0, "targets": 0, "avg_confidence": 0.0},
            candidate_recovery={"latest_success_streak": 0, "latest_run_count": 0},
            lifecycle_stats={"plans": 0, "with_state": 0, "with_attempts": 0},
            gate_chain_stats=gate_chain_stats,
            criteria={"gate_chain_min_full_qualification_rate": threshold},
            manifest_data={},
        )

    def test_gate_chain_key_present_in_assessments(self) -> None:
        result = self._run({})
        self.assertIn("gate_chain", result)

    def test_empty_gate_chain_evidence_not_met(self) -> None:
        result = self._run({})
        self.assertFalse(result["gate_chain"]["evidence_met"])

    def test_passing_gate_chain_evidence_met(self) -> None:
        stats = {"total": 10, "accepted": 8, "full_qualification_rate": 0.7,
                 "gate_coverage": {"g4_repo_quick": 5}}
        result = self._run(stats)
        self.assertTrue(result["gate_chain"]["evidence_met"])

    def test_low_fqr_evidence_not_met(self) -> None:
        stats = {"total": 10, "accepted": 8, "full_qualification_rate": 0.3,
                 "gate_coverage": {"g4_repo_quick": 5}}
        result = self._run(stats)
        self.assertFalse(result["gate_chain"]["evidence_met"])

    def test_zero_g4_evidence_not_met(self) -> None:
        stats = {"total": 10, "accepted": 8, "full_qualification_rate": 0.7,
                 "gate_coverage": {"g4_repo_quick": 0}}
        result = self._run(stats)
        self.assertFalse(result["gate_chain"]["evidence_met"])

    def test_threshold_read_from_criteria(self) -> None:
        stats = {"total": 10, "accepted": 8, "full_qualification_rate": 0.65,
                 "gate_coverage": {"g4_repo_quick": 5}}
        self.assertFalse(self._run(stats, threshold=0.8)["gate_chain"]["evidence_met"])
        self.assertTrue(self._run(stats, threshold=0.6)["gate_chain"]["evidence_met"])

    def test_evidence_snapshot_contains_threshold(self) -> None:
        result = self._run({}, threshold=0.75)
        snapshot = result["gate_chain"]["evidence_snapshot"]
        self.assertEqual(snapshot["threshold"], 0.75)

    def test_evidence_snapshot_contains_fqr(self) -> None:
        stats = {"total": 5, "accepted": 3, "full_qualification_rate": 0.6,
                 "gate_coverage": {"g4_repo_quick": 3}}
        snapshot = self._run(stats)["gate_chain"]["evidence_snapshot"]
        self.assertEqual(snapshot["full_qualification_rate"], 0.6)


class ManifestThresholdSourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "level10_qualify.py").read_text(encoding="utf-8")

    def test_gate_chain_min_full_qualification_rate_in_source(self) -> None:
        self.assertIn("gate_chain_min_full_qualification_rate", self._src)

    def test_gate_chain_threshold_not_hardcoded_in_evaluate_v8_gates(self) -> None:
        import re
        v8_fn_match = re.search(
            r"def evaluate_v8_gates.*?(?=\ndef |\Z)", self._src, re.DOTALL
        )
        self.assertIsNotNone(v8_fn_match)
        v8_body = v8_fn_match.group(0)
        self.assertIn("gate_chain_min_full_qualification_rate", v8_body)

    def test_gate_chain_in_evaluate_subsystems_source(self) -> None:
        self.assertIn("gate_chain_stats", self._src)


class QualifyV3HardGateTest(unittest.TestCase):
    """Tests for --fail-on-incomplete-v8-gates behavior added in qualify-v3."""

    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "level10_qualify.py").read_text(encoding="utf-8")

    def test_fail_on_incomplete_v8_gates_flag_present(self) -> None:
        self.assertIn("fail-on-incomplete-v8-gates", self._src)

    def test_fail_on_incomplete_v8_gates_arg_added(self) -> None:
        self.assertIn("fail_on_incomplete_v8_gates", self._src)

    def test_exit_1_when_not_all_ready(self) -> None:
        import re
        main_fn = re.search(r"def main\(\).*?(?=\ndef |\Z)", self._src, re.DOTALL)
        self.assertIsNotNone(main_fn)
        body = main_fn.group(0)
        self.assertIn("fail_on_incomplete_v8_gates", body)
        self.assertIn("all_ready", body)
        self.assertIn("return 1", body)

    def test_fail_stderr_message_present(self) -> None:
        self.assertIn("[qualify] FAIL", self._src)

    def test_all_ready_false_triggers_exit(self) -> None:
        import re
        self.assertRegex(
            self._src,
            r"fail_on_incomplete_v8_gates.*?all_ready|all_ready.*?fail_on_incomplete_v8_gates",
        )


if __name__ == "__main__":
    unittest.main()
