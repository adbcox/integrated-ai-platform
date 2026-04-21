"""Conformance tests for framework/terminal_autonomy_ratifier.py (LARAC2-TERMINAL-RATIFIER-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.terminal_autonomy_ratifier import (
    RatificationCriterion, TerminalRatificationRecord,
    TerminalAutonomyRatifier, emit_terminal_ratification,
)
from framework.adapter_readiness_stress import StressHarnessResult
from framework.controlled_adapter_scaffold import AdapterScaffoldPlan, ScaffoldGate
from framework.adapter_campaign_pre_authorizer import RatificationArtifact


def _stress(verdict="stable", blocking_failures=0):
    return StressHarnessResult(
        verdict=verdict, checks=[], blocking_failures=blocking_failures,
        quality_score=0.75, analyzed_at="2026-01-01T00:00:00+00:00", artifact_path=None,
    )


def _scaffold(scaffold_decision="proceed", gates_passed=2, gates_total=2, campaign_id="c1"):
    return AdapterScaffoldPlan(
        scaffold_decision=scaffold_decision,
        gates=[],
        gates_passed=gates_passed,
        gates_total=gates_total,
        defer_reasons=[],
        campaign_id=campaign_id,
        scaffolded_at="2026-01-01T00:00:00+00:00",
        artifact_path=None,
    )


def _ratification(decision="ratified", all_criteria_passed=True, campaign_id="c1"):
    return RatificationArtifact(
        campaign_id=campaign_id,
        decision=decision,
        ratified_at="2026-01-01T00:00:00+00:00",
        total_attempts=1,
        all_criteria_passed=all_criteria_passed,
        criteria_summary={},
        defer_reasons=[],
        next_steps=[],
        artifact_path=None,
    )


# --- import and type ---

def test_import_ratifier():
    assert callable(TerminalAutonomyRatifier)


def test_returns_terminal_ratification_record():
    record = TerminalAutonomyRatifier().ratify()
    assert isinstance(record, TerminalRatificationRecord)


# --- all-none blocked ---

def test_all_none_blocked():
    record = TerminalAutonomyRatifier().ratify()
    assert record.terminal_verdict == "blocked"


def test_all_none_criteria_all_fail():
    record = TerminalAutonomyRatifier().ratify()
    assert record.criteria_passed == 0


# --- stress criterion ---

def test_stress_stable_criterion_passes():
    record = TerminalAutonomyRatifier().ratify(stress_result=_stress("stable"))
    c = next(x for x in record.criteria if x.criterion_name == "stress_stable")
    assert c.passed is True


def test_stress_unstable_criterion_fails():
    record = TerminalAutonomyRatifier().ratify(stress_result=_stress("unstable", 1))
    c = next(x for x in record.criteria if x.criterion_name == "stress_stable")
    assert c.passed is False


# --- scaffold criterion ---

def test_scaffold_proceed_criterion_passes():
    record = TerminalAutonomyRatifier().ratify(scaffold_plan=_scaffold("proceed"))
    c = next(x for x in record.criteria if x.criterion_name == "scaffold_proceed")
    assert c.passed is True


def test_scaffold_defer_criterion_fails():
    record = TerminalAutonomyRatifier().ratify(scaffold_plan=_scaffold("defer"))
    c = next(x for x in record.criteria if x.criterion_name == "scaffold_proceed")
    assert c.passed is False


# --- ratification criterion ---

def test_ratification_approved_criterion_passes():
    record = TerminalAutonomyRatifier().ratify(ratification_artifact=_ratification("ratified", True))
    c = next(x for x in record.criteria if x.criterion_name == "ratification_approved")
    assert c.passed is True


def test_ratification_deferred_criterion_fails():
    record = TerminalAutonomyRatifier().ratify(ratification_artifact=_ratification("deferred", False))
    c = next(x for x in record.criteria if x.criterion_name == "ratification_approved")
    assert c.passed is False


def test_ratification_not_all_criteria_passed_fails():
    record = TerminalAutonomyRatifier().ratify(ratification_artifact=_ratification("ratified", False))
    c = next(x for x in record.criteria if x.criterion_name == "ratification_approved")
    assert c.passed is False


# --- ratified / deferred verdicts ---

def test_ratified_when_all_pass():
    record = TerminalAutonomyRatifier().ratify(
        stress_result=_stress("stable"),
        scaffold_plan=_scaffold("proceed"),
        ratification_artifact=_ratification("ratified", True),
    )
    assert record.terminal_verdict == "ratified"
    assert record.criteria_passed == 3
    assert record.blocking_reasons == []


def test_deferred_when_one_fails():
    record = TerminalAutonomyRatifier().ratify(
        stress_result=_stress("unstable", 1),
        scaffold_plan=_scaffold("proceed"),
        ratification_artifact=_ratification("ratified", True),
    )
    assert record.terminal_verdict == "deferred"
    assert len(record.blocking_reasons) >= 1


# --- campaign_id propagation ---

def test_campaign_id_from_scaffold():
    record = TerminalAutonomyRatifier().ratify(scaffold_plan=_scaffold(campaign_id="my-camp"))
    assert record.campaign_id == "my-camp"


def test_campaign_id_from_ratification_when_no_scaffold():
    record = TerminalAutonomyRatifier().ratify(ratification_artifact=_ratification(campaign_id="rat-camp"))
    assert record.campaign_id == "rat-camp"


def test_campaign_id_none_when_all_absent():
    record = TerminalAutonomyRatifier().ratify()
    assert record.campaign_id is None


# --- criteria structure ---

def test_criteria_list_length():
    record = TerminalAutonomyRatifier().ratify()
    assert len(record.criteria) == 3


def test_criteria_are_ratification_criterion():
    record = TerminalAutonomyRatifier().ratify()
    for c in record.criteria:
        assert isinstance(c, RatificationCriterion)


# --- artifact ---

def test_artifact_written(tmp_path):
    record = TerminalAutonomyRatifier().ratify()
    path = emit_terminal_ratification(record, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    record = TerminalAutonomyRatifier().ratify()
    path = emit_terminal_ratification(record, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "terminal_verdict" in data
    assert "criteria" in data
    assert "blocking_reasons" in data


def test_artifact_path_set(tmp_path):
    record = TerminalAutonomyRatifier().ratify()
    path = emit_terminal_ratification(record, artifact_dir=tmp_path)
    assert record.artifact_path == path


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "TerminalAutonomyRatifier")
    assert hasattr(framework, "TerminalRatificationRecord")
    assert hasattr(framework, "RatificationCriterion")
    assert hasattr(framework, "emit_terminal_ratification")
