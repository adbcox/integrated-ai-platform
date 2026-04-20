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


if __name__ == "__main__":
    unittest.main()
