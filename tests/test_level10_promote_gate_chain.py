from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.level10_promote import (
    LaneDecision,
    build_subsystem_gate_matrix,
    enforce_subsystem_gate_policy,
)


def _summary(gate_chain_ready: bool, **extra_gates: bool) -> dict:
    gates = {
        "promotion8_ready": True,
        "qualification8_ready": True,
        "stage8_ready": True,
        "manager8_ready": True,
        "rag8_ready": True,
        "worker8_ready": True,
        "gate_chain_ready": gate_chain_ready,
    }
    gates.update(extra_gates)
    return {"v8_gate_assertions": {"gates": gates}}


class BuildGateMatrixTest(unittest.TestCase):
    def test_gate_chain_ready_true_not_blocked_candidate(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=True))
        self.assertNotIn("gate_chain_ready", matrix["candidate_promote_blocked"])

    def test_gate_chain_ready_true_not_blocked_stage6(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=True))
        self.assertNotIn("gate_chain_ready", matrix["stage6_promote_blocked"])

    def test_gate_chain_ready_false_blocked_candidate(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        self.assertIn("gate_chain_ready", matrix["candidate_promote_blocked"])

    def test_gate_chain_ready_false_blocked_stage6(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        self.assertIn("gate_chain_ready", matrix["stage6_promote_blocked"])

    def test_gate_chain_ready_absent_treated_as_false_candidate(self) -> None:
        summary = {"v8_gate_assertions": {"gates": {}}}
        matrix = build_subsystem_gate_matrix(summary)
        self.assertIn("gate_chain_ready", matrix["candidate_promote_blocked"])

    def test_gate_chain_ready_absent_treated_as_false_stage6(self) -> None:
        summary = {"v8_gate_assertions": {"gates": {}}}
        matrix = build_subsystem_gate_matrix(summary)
        self.assertIn("gate_chain_ready", matrix["stage6_promote_blocked"])

    def test_gate_chain_ready_in_candidate_promote_requires(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=True))
        self.assertIn("gate_chain_ready", matrix["candidate_promote_requires"])

    def test_gate_chain_ready_in_stage6_promote_requires(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=True))
        self.assertIn("gate_chain_ready", matrix["stage6_promote_requires"])


class EnforceGateChainBlockTest(unittest.TestCase):
    def _candidate_promote(self) -> LaneDecision:
        return LaneDecision(
            lane="candidate",
            action="promote",
            reason="met",
            next_status="ready_for_promotion",
        )

    def _stage6_promote(self) -> LaneDecision:
        return LaneDecision(
            lane="stage6",
            action="promote",
            reason="met",
            next_status="candidate_ready",
        )

    def test_candidate_promote_becomes_hold_when_gate_chain_false(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        result = enforce_subsystem_gate_policy([self._candidate_promote()], matrix)
        self.assertEqual(result[0].action, "hold")

    def test_stage6_promote_becomes_hold_when_gate_chain_false(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        result = enforce_subsystem_gate_policy([self._stage6_promote()], matrix)
        self.assertEqual(result[0].action, "hold")

    def test_candidate_promote_passes_when_gate_chain_true(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=True))
        result = enforce_subsystem_gate_policy([self._candidate_promote()], matrix)
        self.assertEqual(result[0].action, "promote")

    def test_stage6_promote_passes_when_gate_chain_true(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=True))
        result = enforce_subsystem_gate_policy([self._stage6_promote()], matrix)
        self.assertEqual(result[0].action, "promote")

    def test_hold_decision_unaffected_by_gate_chain(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        hold = LaneDecision(
            lane="candidate",
            action="hold",
            reason="low",
            next_status="in_progress",
        )
        result = enforce_subsystem_gate_policy([hold], matrix)
        self.assertEqual(result[0].action, "hold")

    def test_demote_decision_unaffected_by_gate_chain(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        demote = LaneDecision(
            lane="candidate",
            action="demote",
            reason="bad",
            next_status="blocked",
        )
        result = enforce_subsystem_gate_policy([demote], matrix)
        self.assertEqual(result[0].action, "demote")

    def test_hold_reason_mentions_gate_chain_when_blocked(self) -> None:
        matrix = build_subsystem_gate_matrix(_summary(gate_chain_ready=False))
        result = enforce_subsystem_gate_policy([self._candidate_promote()], matrix)
        self.assertIn("gate_chain_ready", result[0].reason)


class SourceAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "level10_promote.py").read_text(encoding="utf-8")

    def test_gate_chain_ready_in_candidate_promote_requires_source(self) -> None:
        self.assertIn("gate_chain_ready", self._src)

    def test_gate_chain_stats_in_audit_record_source(self) -> None:
        self.assertIn("gate_chain_stats", self._src)

    def test_gate_chain_ready_appears_in_stage6_block_source(self) -> None:
        idx_candidate = self._src.index("candidate_promote_requires")
        idx_stage6 = self._src.index("stage6_promote_requires")
        candidate_slice = self._src[idx_candidate:idx_stage6]
        stage6_slice = self._src[idx_stage6:idx_stage6 + 400]
        self.assertIn("gate_chain_ready", candidate_slice)
        self.assertIn("gate_chain_ready", stage6_slice)


class PreviewDecisionGateChainTest(unittest.TestCase):
    """Verify gate_chain participates in _preview_decision core_ready check."""

    def _assessments(self, gate_chain_met: bool) -> dict:
        base = {
            name: {"evidence_met": True}
            for name in ("stage_system", "manager_system", "rag_system", "regression_framework")
        }
        base["gate_chain"] = {"evidence_met": gate_chain_met}
        return base

    def _preview_summary(self, gate_chain_met: bool, successes: int = 5) -> dict:
        return {
            "metrics": {
                "stage6_preview": {"success": successes, "failure": 0},
            },
            "subsystem_assessments": self._assessments(gate_chain_met),
        }

    def _criteria(self) -> dict:
        return {"stage6_success_threshold": 3, "stage6_failure_budget": 1}

    def test_preview_promote_blocked_when_gate_chain_false(self) -> None:
        from bin.level10_promote import _preview_decision
        decision = _preview_decision(
            self._preview_summary(gate_chain_met=False),
            self._criteria(),
            "building",
        )
        self.assertNotEqual(decision.action, "promote")

    def test_preview_promote_passes_when_gate_chain_true(self) -> None:
        from bin.level10_promote import _preview_decision
        decision = _preview_decision(
            self._preview_summary(gate_chain_met=True),
            self._criteria(),
            "building",
        )
        self.assertEqual(decision.action, "promote")

    def test_preview_hold_reason_when_gate_chain_false(self) -> None:
        from bin.level10_promote import _preview_decision
        decision = _preview_decision(
            self._preview_summary(gate_chain_met=False),
            self._criteria(),
            "building",
        )
        self.assertIn("core_ready=False", decision.reason)

    def test_gate_chain_missing_from_assessments_blocks_promote(self) -> None:
        from bin.level10_promote import _preview_decision
        summary = {
            "metrics": {"stage6_preview": {"success": 5, "failure": 0}},
            "subsystem_assessments": {
                name: {"evidence_met": True}
                for name in ("stage_system", "manager_system", "rag_system", "regression_framework")
            },
        }
        decision = _preview_decision(summary, self._criteria(), "building")
        self.assertNotEqual(decision.action, "promote")


class PromoteSourceGateChainAssertionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._src = (REPO_ROOT / "bin" / "level10_promote.py").read_text(encoding="utf-8")

    def test_gate_chain_in_core_ready_tuple(self) -> None:
        import re
        preview_fn = re.search(
            r"def _preview_decision.*?(?=\ndef |\Z)", self._src, re.DOTALL
        )
        self.assertIsNotNone(preview_fn)
        self.assertIn("gate_chain", preview_fn.group(0))


if __name__ == "__main__":
    unittest.main()
