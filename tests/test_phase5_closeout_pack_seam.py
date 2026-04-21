"""Seam tests for P5-01: Phase 5 Closeout Qualification Pack."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase5_closeout_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase5_closeout_baseline.v1.yaml"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Import seams
# ─────────────────────────────────────────────────────────────────────────────

def test_import_unified_validation_artifact_v1():
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    assert UnifiedValidationArtifactV1 is not None


def test_import_qualification_readiness_v1():
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    assert QualificationReadinessEvaluatorV1 is not None


def test_import_local_autonomy_gate_v1():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    assert LocalAutonomyGateEvaluatorV1 is not None


def test_import_regression_summary_v1():
    from framework.regression_summary_v1 import RegressionSummaryV1
    assert RegressionSummaryV1 is not None


def test_import_phase5_closeout_v1():
    from framework.phase5_closeout_v1 import Phase5CloseoutV1
    assert Phase5CloseoutV1 is not None


# ─────────────────────────────────────────────────────────────────────────────
# 2. UnifiedValidationArtifactV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_unified_artifact_build_pass():
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    art = UnifiedValidationArtifactV1.build(
        package_id="TEST-PKG-001",
        package_label="SUBSTRATE",
        validation_results={"step_a": True, "step_b": True},
        escalation_status="NOT_ESCALATED",
    )
    assert art.all_passed is True
    assert art.final_outcome == "PASS"
    assert art.pass_rate == 1.0


def test_unified_artifact_build_fail():
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    art = UnifiedValidationArtifactV1.build(
        package_id="TEST-PKG-002",
        package_label="SUBSTRATE",
        validation_results={"step_a": True, "step_b": False},
        escalation_status="NOT_ESCALATED",
    )
    assert art.all_passed is False
    assert art.final_outcome == "FAIL"
    assert art.pass_rate == 0.5


def test_unified_artifact_to_dict_fields():
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    art = UnifiedValidationArtifactV1.build(
        package_id="TEST-PKG-003",
        package_label="SUBSTRATE",
        validation_results={"x": True},
        artifacts_produced=["artifacts/substrate/test.json"],
        escalation_status="NOT_ESCALATED",
    )
    d = art.to_dict()
    for field in ("package_id", "package_label", "validations_run", "validation_results",
                  "artifacts_produced", "escalation_status", "final_outcome",
                  "generated_at", "all_passed", "pass_rate"):
        assert field in d, f"missing field: {field}"


def test_unified_artifact_escalation_status_present():
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    art = UnifiedValidationArtifactV1.build(
        package_id="TEST-PKG-004",
        package_label="SUBSTRATE",
        validation_results={"a": True},
        escalation_status="NOT_ESCALATED",
    )
    assert art.escalation_status == "NOT_ESCALATED"


def test_unified_artifact_validations_run_matches_results():
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    results = {"modules_loaded": True, "regression_cases": True, "qualification_readiness": True}
    art = UnifiedValidationArtifactV1.build(
        package_id="TEST-PKG-005",
        package_label="SUBSTRATE",
        validation_results=results,
        escalation_status="NOT_ESCALATED",
    )
    assert set(art.validations_run) == set(results.keys())


# ─────────────────────────────────────────────────────────────────────────────
# 3. QualificationReadinessEvaluatorV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_qualification_ready_when_all_met():
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    ev = QualificationReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=1.0,
        escalation_status_present=True,
    )
    assert result.readiness_ready is True
    assert result.blocking_gaps == []


def test_qualification_blocks_on_low_pass_rate():
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    ev = QualificationReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=0.50,
        escalation_status_present=True,
    )
    assert result.readiness_ready is False
    assert any("validation_pass_rate" in g for g in result.blocking_gaps)


def test_qualification_blocks_on_missing_artifact():
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    ev = QualificationReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=False,
        validation_pass_rate=1.0,
        escalation_status_present=True,
    )
    assert result.readiness_ready is False
    assert any("artifact_completeness" in g for g in result.blocking_gaps)


def test_qualification_blocks_on_missing_escalation():
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    ev = QualificationReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=1.0,
        escalation_status_present=False,
    )
    assert result.readiness_ready is False
    assert any("escalation_accounting" in g for g in result.blocking_gaps)


def test_qualification_result_to_dict_fields():
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    ev = QualificationReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=True, validation_pass_rate=1.0, escalation_status_present=True
    )
    d = result.to_dict()
    for field in ("artifact_completeness", "validation_pass_rate", "escalation_accounting",
                  "readiness_ready", "blocking_gaps", "evidence_summary"):
        assert field in d, f"missing field: {field}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. LocalAutonomyGateEvaluatorV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_autonomy_gate_passes_all_signals():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    ev = LocalAutonomyGateEvaluatorV1()
    result = ev.evaluate(
        first_pass_success_rate=1.0,
        retries_within_budget=True,
        escalation_rate=0.0,
        artifact_completeness_signal=True,
    )
    assert result.gate_passed is True
    assert result.gate_blockers == []


def test_autonomy_gate_blocks_on_low_first_pass():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    ev = LocalAutonomyGateEvaluatorV1()
    result = ev.evaluate(
        first_pass_success_rate=0.25,
        retries_within_budget=True,
        escalation_rate=0.0,
        artifact_completeness_signal=True,
    )
    assert result.gate_passed is False
    assert any("first_pass_success_signal" in b for b in result.gate_blockers)


def test_autonomy_gate_blocks_on_retry_overrun():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    ev = LocalAutonomyGateEvaluatorV1()
    result = ev.evaluate(
        first_pass_success_rate=1.0,
        retries_within_budget=False,
        escalation_rate=0.0,
        artifact_completeness_signal=True,
    )
    assert result.gate_passed is False
    assert any("retry_discipline_signal" in b for b in result.gate_blockers)


def test_autonomy_gate_blocks_on_high_escalation():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    ev = LocalAutonomyGateEvaluatorV1()
    result = ev.evaluate(
        first_pass_success_rate=1.0,
        retries_within_budget=True,
        escalation_rate=0.50,
        artifact_completeness_signal=True,
    )
    assert result.gate_passed is False
    assert any("escalation_rate_signal" in b for b in result.gate_blockers)


def test_autonomy_gate_to_dict_fields():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    ev = LocalAutonomyGateEvaluatorV1()
    result = ev.evaluate(
        first_pass_success_rate=1.0, retries_within_budget=True,
        escalation_rate=0.0, artifact_completeness_signal=True
    )
    d = result.to_dict()
    for field in ("gate_passed", "gate_reasons", "gate_blockers", "signal_summary"):
        assert field in d, f"missing field: {field}"


def test_autonomy_gate_gate_reasons_non_empty_on_pass():
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    ev = LocalAutonomyGateEvaluatorV1()
    result = ev.evaluate(
        first_pass_success_rate=1.0, retries_within_budget=True,
        escalation_rate=0.0, artifact_completeness_signal=True
    )
    assert len(result.gate_reasons) == 4


# ─────────────────────────────────────────────────────────────────────────────
# 5. RegressionSummaryV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_regression_summary_from_cases_all_pass():
    from framework.regression_summary_v1 import RegressionSummaryV1, RegressionCaseV1
    cases = [
        RegressionCaseV1(case_id="r1", task_class="bug_fix", passed=True),
        RegressionCaseV1(case_id="r2", task_class="narrow_feature", passed=True),
        RegressionCaseV1(case_id="r3", task_class="reporting_helper", passed=True),
    ]
    summary = RegressionSummaryV1.from_cases(cases)
    assert summary.regression_cases_run == 3
    assert summary.regression_cases_passed == 3
    assert summary.pass_rate == 1.0
    assert summary.failure_modes == []


def test_regression_summary_with_failure():
    from framework.regression_summary_v1 import RegressionSummaryV1, RegressionCaseV1
    cases = [
        RegressionCaseV1(case_id="r1", task_class="bug_fix", passed=True),
        RegressionCaseV1(case_id="r2", task_class="test_addition", passed=False,
                         failure_mode="assertion_mismatch"),
    ]
    summary = RegressionSummaryV1.from_cases(cases)
    assert summary.pass_rate == 0.5
    assert "assertion_mismatch" in summary.failure_modes


def test_regression_summary_to_dict_fields():
    from framework.regression_summary_v1 import RegressionSummaryV1, RegressionCaseV1
    cases = [RegressionCaseV1(case_id="r1", task_class="bug_fix", passed=True)]
    summary = RegressionSummaryV1.from_cases(cases)
    d = summary.to_dict()
    for field in ("regression_cases_run", "regression_cases_passed", "pass_rate",
                  "failure_modes", "cases"):
        assert field in d, f"missing field: {field}"


def test_regression_case_to_dict():
    from framework.regression_summary_v1 import RegressionCaseV1
    case = RegressionCaseV1(case_id="r1", task_class="bug_fix", passed=True)
    d = case.to_dict()
    assert d["case_id"] == "r1"
    assert d["passed"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 6. Phase5CloseoutV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_closeout_inputs(all_pass: bool = True):
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    from framework.local_autonomy_gate_v1 import LocalAutonomyGateEvaluatorV1
    from framework.regression_summary_v1 import RegressionSummaryV1, RegressionCaseV1

    art = UnifiedValidationArtifactV1.build(
        package_id="TEST-CO-001",
        package_label="SUBSTRATE",
        validation_results={"step_a": True, "step_b": True},
        escalation_status="NOT_ESCALATED",
    )
    qual_ev = QualificationReadinessEvaluatorV1()
    qual = qual_ev.evaluate(
        artifact_complete=True, validation_pass_rate=1.0, escalation_status_present=True
    )
    gate_ev = LocalAutonomyGateEvaluatorV1()
    gate = gate_ev.evaluate(
        first_pass_success_rate=1.0, retries_within_budget=True,
        escalation_rate=0.0, artifact_completeness_signal=True
    )
    cases = [RegressionCaseV1(case_id=f"r{i}", task_class="bug_fix", passed=all_pass)
             for i in range(3)]
    reg = RegressionSummaryV1.from_cases(cases)
    return art, qual, gate, reg


def test_closeout_assemble_returns_record():
    from framework.phase5_closeout_v1 import Phase5CloseoutV1
    art, qual, gate, reg = _make_closeout_inputs()
    co = Phase5CloseoutV1()
    record = co.assemble(
        package_id="TEST-CO-001",
        unified_artifact=art,
        qualification_result=qual,
        autonomy_gate_result=gate,
        regression_summary=reg,
        escalation_status="NOT_ESCALATED",
    )
    assert record is not None
    assert record.phase_id == "phase_5"


def test_closeout_promotion_ready_when_all_pass():
    from framework.phase5_closeout_v1 import Phase5CloseoutV1
    art, qual, gate, reg = _make_closeout_inputs(all_pass=True)
    co = Phase5CloseoutV1()
    record = co.assemble(
        package_id="TEST-CO-002",
        unified_artifact=art,
        qualification_result=qual,
        autonomy_gate_result=gate,
        regression_summary=reg,
    )
    assert record.promotion_readiness_ready is True


def test_closeout_to_dict_fields():
    from framework.phase5_closeout_v1 import Phase5CloseoutV1
    art, qual, gate, reg = _make_closeout_inputs()
    co = Phase5CloseoutV1()
    record = co.assemble(
        package_id="TEST-CO-003",
        unified_artifact=art,
        qualification_result=qual,
        autonomy_gate_result=gate,
        regression_summary=reg,
    )
    d = record.to_dict()
    for field in ("phase_id", "package_id", "generated_at", "unified_artifact",
                  "qualification_result", "autonomy_gate_result", "regression_summary",
                  "escalation_status", "promotion_readiness_ready", "closing_notes"):
        assert field in d, f"missing field: {field}"


def test_closeout_escalation_status_present():
    from framework.phase5_closeout_v1 import Phase5CloseoutV1
    art, qual, gate, reg = _make_closeout_inputs()
    co = Phase5CloseoutV1()
    record = co.assemble(
        package_id="TEST-CO-004",
        unified_artifact=art,
        qualification_result=qual,
        autonomy_gate_result=gate,
        regression_summary=reg,
        escalation_status="NOT_ESCALATED",
    )
    assert record.escalation_status == "NOT_ESCALATED"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Phase 5 closeout baseline content seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_closeout_baseline():
    if not BASELINE_PATH.exists():
        pytest.skip("phase5_closeout_baseline.v1.yaml not found")
    try:
        import yaml
        return yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8"))
    except ImportError:
        import re
        data = {}
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if m:
                data[m.group(1)] = True
        return data


def test_closeout_baseline_phase_id():
    data = _load_closeout_baseline()
    assert data.get("phase_id") == "phase_5"


def test_closeout_baseline_required_modules_present():
    data = _load_closeout_baseline()
    rm = data.get("required_modules", {})
    required = [
        "unified_validation_artifact_v1",
        "qualification_readiness_v1",
        "local_autonomy_gate_v1",
        "regression_summary_v1",
        "phase5_closeout_v1",
    ]
    if isinstance(rm, dict):
        for name in required:
            assert name in rm, f"required_modules missing: {name}"
    else:
        pytest.skip("yaml not available; required_modules not fully parsed")


def test_closeout_baseline_has_required_capabilities():
    data = _load_closeout_baseline()
    assert "required_capabilities" in data


def test_closeout_baseline_has_completion_requirements():
    data = _load_closeout_baseline()
    assert "completion_requirements" in data


def test_closeout_baseline_has_remaining_blockers():
    data = _load_closeout_baseline()
    assert "remaining_blockers" in data


def test_closeout_baseline_has_promotion_readiness_gate():
    data = _load_closeout_baseline()
    assert "promotion_readiness_gate" in data


# ─────────────────────────────────────────────────────────────────────────────
# 8. Artifact structure seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_artifact():
    if not ARTIFACT_PATH.exists():
        pytest.skip("phase5_closeout_pack_check.json not yet emitted; run the runner first")
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_artifact_phase5_pack_field():
    d = _load_artifact()
    assert d["phase5_pack"] == "qualification_and_readiness_closeout_v1"


def test_artifact_all_checks_passed():
    d = _load_artifact()
    assert d["all_checks_passed"] is True


def test_artifact_qualification_evaluated():
    d = _load_artifact()
    assert d["qualification_evaluated"] is True


def test_artifact_local_autonomy_gate_evaluated():
    d = _load_artifact()
    assert d["local_autonomy_gate_evaluated"] is True


def test_artifact_regression_cases_run_gte_3():
    d = _load_artifact()
    assert d["regression_cases_run"] >= 3


def test_artifact_promotion_readiness_ready_present():
    d = _load_artifact()
    assert "promotion_readiness_ready" in d
    assert isinstance(d["promotion_readiness_ready"], bool)


def test_artifact_escalation_status_present():
    d = _load_artifact()
    assert d.get("escalation_status") == "NOT_ESCALATED"


def test_artifact_component_summary_has_5_modules():
    d = _load_artifact()
    cs = d.get("component_summary", [])
    module_entries = [e for e in cs if "module" in e and "framework" in e.get("module", "")]
    assert len(module_entries) >= 5


def test_artifact_required_modules_loaded():
    d = _load_artifact()
    assert d["required_modules_loaded"] is True


def test_artifact_regression_pass_rate_gte_75():
    d = _load_artifact()
    assert d["regression_pass_rate"] >= 0.75


def test_artifact_generated_at_present():
    d = _load_artifact()
    assert "generated_at" in d
    assert d["generated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# 9. Runner existence seam
# ─────────────────────────────────────────────────────────────────────────────

def test_runner_exists():
    runner = REPO_ROOT / "bin/run_phase5_closeout_pack_check.py"
    assert runner.exists(), f"runner not found: {runner}"


def test_seam_test_file_exists():
    seam = REPO_ROOT / "tests/test_phase5_closeout_pack_seam.py"
    assert seam.exists(), f"seam test file not found: {seam}"
