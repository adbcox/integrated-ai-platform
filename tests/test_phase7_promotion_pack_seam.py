"""Seam tests for P7-01: Phase 7 Live Local-First Closeout and Promotion Pack."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase7_promotion_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase7_promotion_baseline.v1.yaml"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Import seams
# ─────────────────────────────────────────────────────────────────────────────

def test_import_persistent_execution_ledger_v1():
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    assert PersistentExecutionLedgerV1 is not None


def test_import_live_aider_dispatch_v1():
    from framework.live_aider_dispatch_v1 import LiveAiderDispatchV1
    assert LiveAiderDispatchV1 is not None


def test_import_local_autonomy_telemetry_bridge_v1():
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    assert LocalAutonomyTelemetryBridgeV1 is not None


def test_import_escalation_workflow_v1():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    assert EscalationWorkflowV1 is not None


def test_import_phase6_closeout_ratifier_v1():
    from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutRatifierV1
    assert Phase6CloseoutRatifierV1 is not None


def test_import_phase7_promotion_v1():
    from framework.phase7_promotion_v1 import Phase7PromotionV1
    assert Phase7PromotionV1 is not None


# ─────────────────────────────────────────────────────────────────────────────
# 2. PersistentExecutionLedgerV1 seams
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_ledger():
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    with tempfile.TemporaryDirectory() as tmp:
        ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "test_ledger.jsonl")
        yield ledger


def test_ledger_append_and_reload(tmp_ledger):
    tmp_ledger.append_record(
        run_id="r001", package_id="PKG1", package_label="SUBSTRATE",
        executor="aider", route="local_fast",
        validation_results={"make_check": True},
    )
    records = tmp_ledger.load_records()
    assert len(records) == 1
    assert records[0].run_id == "r001"
    assert records[0].executor == "aider"


def test_ledger_persists_multiple_records(tmp_ledger):
    for i in range(3):
        tmp_ledger.append_record(
            run_id=f"r{i:03d}", package_id="PKG1", package_label="SUBSTRATE",
            executor="aider", route="local_fast",
            validation_results={"ok": True},
        )
    records = tmp_ledger.load_records()
    assert len(records) == 3


def test_ledger_summarize_fields(tmp_ledger):
    tmp_ledger.append_record(
        run_id="r001", package_id="P1", package_label="SUBSTRATE",
        executor="aider", route="local_fast",
        validation_results={"a": True},
    )
    s = tmp_ledger.summarize()
    for field in ("total_runs", "passed_runs", "pass_rate", "executor_counts", "ledger_path"):
        assert field in s, f"missing field: {field}"


def test_ledger_entry_to_dict_fields(tmp_ledger):
    entry = tmp_ledger.append_record(
        run_id="r001", package_id="P1", package_label="SUBSTRATE",
        executor="aider", route="local_fast",
        validation_results={"a": True},
    )
    d = entry.to_dict()
    for field in ("run_id", "package_id", "executor", "route", "validations_run",
                  "validation_results", "escalation_status", "final_outcome", "recorded_at"):
        assert field in d, f"missing field: {field}"


def test_ledger_pass_rate_computed(tmp_ledger):
    tmp_ledger.append_record("r1", "P1", "S", "aider", "lf", {"ok": True})
    tmp_ledger.append_record("r2", "P1", "S", "aider", "lf", {"ok": False})
    s = tmp_ledger.summarize()
    assert s["pass_rate"] == 0.5


def test_ledger_from_dict_roundtrip(tmp_ledger):
    entry = tmp_ledger.append_record(
        run_id="r001", package_id="P1", package_label="SUBSTRATE",
        executor="aider", route="local_fast",
        validation_results={"x": True},
        notes=["test note"],
    )
    reloaded = tmp_ledger.load_records()
    assert reloaded[0].notes == ["test note"]
    assert reloaded[0].final_outcome == "PASS"


# ─────────────────────────────────────────────────────────────────────────────
# 3. LiveAiderDispatchV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_dispatch_dry_run_returns_record():
    from framework.live_aider_dispatch_v1 import LiveAiderDispatchV1
    d = LiveAiderDispatchV1()
    rec = d.dispatch(
        package_id="PKG1",
        allowed_files=["framework/x.py"],
        message="run tests",
        dry_run=True,
    )
    assert rec.dispatch_status == "dry_run"
    assert rec.execution_mode == "local_first"
    assert rec.exit_code is None


def test_dispatch_blocked_when_no_files():
    from framework.live_aider_dispatch_v1 import LiveAiderDispatchV1
    d = LiveAiderDispatchV1()
    rec = d.dispatch(package_id="PKG1", allowed_files=[], message="run", dry_run=True)
    assert rec.dispatch_status == "blocked"


def test_dispatch_to_dict_fields():
    from framework.live_aider_dispatch_v1 import LiveAiderDispatchV1
    d = LiveAiderDispatchV1()
    rec = d.dispatch(package_id="PKG1", allowed_files=["x.py"], message="m", dry_run=True)
    rd = rec.to_dict()
    for field in ("package_id", "allowed_files", "validation_sequence",
                  "execution_mode", "dispatch_command", "dispatch_status", "dispatched_at"):
        assert field in rd, f"missing field: {field}"


def test_dispatch_execution_mode_local_first():
    from framework.live_aider_dispatch_v1 import LiveAiderDispatchV1
    d = LiveAiderDispatchV1()
    rec = d.dispatch(package_id="P1", allowed_files=["f.py"], message="m", dry_run=True)
    assert rec.execution_mode == "local_first"


def test_dispatch_live_blocked_when_aider_not_installed():
    from framework.live_aider_dispatch_v1 import LiveAiderDispatchV1
    d = LiveAiderDispatchV1()
    rec = d.dispatch(
        package_id="P1", allowed_files=["f.py"], message="run",
        dry_run=False,
    )
    # Will be blocked (aider not on PATH) or completed/failed
    assert rec.dispatch_status in ("blocked", "completed", "failed")


# ─────────────────────────────────────────────────────────────────────────────
# 4. LocalAutonomyTelemetryBridgeV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_telemetry_inputs(executor="aider", n_runs=3, pass_all=True):
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1

    # Use mkdtemp so the directory outlives this function call
    tmp = tempfile.mkdtemp()
    ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "l.jsonl")
    for i in range(n_runs):
        ledger.append_record(
            run_id=f"r{i}", package_id="P1", package_label="S",
            executor=executor, route="local_fast",
            validation_results={"ok": pass_all},
        )

    art = UnifiedValidationArtifactV1.build(
        package_id="P1", package_label="S",
        validation_results={"a": True}, escalation_status="NOT_ESCALATED",
    )
    qual_ev = QualificationReadinessEvaluatorV1()
    qual = qual_ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=1.0 if pass_all else 0.0,
        escalation_status_present=True,
    )
    return ledger, art, qual


def test_telemetry_routine_ready_on_local_runs():
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    ledger, art, qual = _make_telemetry_inputs(executor="aider", pass_all=True)
    bridge = LocalAutonomyTelemetryBridgeV1()
    ev = bridge.derive(ledger, art, qual)
    assert ev.routine_local_execution_ready is True
    assert ev.first_pass_success_signal is True
    assert ev.artifact_completeness_signal is True


def test_telemetry_not_ready_when_no_local_runs():
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1

    with tempfile.TemporaryDirectory() as tmp:
        ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "l.jsonl")
        art = UnifiedValidationArtifactV1.build(
            package_id="P1", package_label="S",
            validation_results={"a": True}, escalation_status="NOT_ESCALATED",
        )
        qual_ev = QualificationReadinessEvaluatorV1()
        qual = qual_ev.evaluate(True, 1.0, True)
        bridge = LocalAutonomyTelemetryBridgeV1()
        ev = bridge.derive(ledger, art, qual)
    assert ev.routine_local_execution_ready is False
    assert len(ev.evidence_gaps) > 0


def test_telemetry_to_dict_fields():
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    ledger, art, qual = _make_telemetry_inputs()
    bridge = LocalAutonomyTelemetryBridgeV1()
    ev = bridge.derive(ledger, art, qual)
    d = ev.to_dict()
    for field in ("routine_local_execution_ready", "first_pass_success_signal",
                  "retry_discipline_signal", "escalation_rate_signal",
                  "artifact_completeness_signal", "evidence_gaps", "signal_detail"):
        assert field in d, f"missing field: {field}"


def test_telemetry_high_escalation_blocks():
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    ledger, art, qual = _make_telemetry_inputs()
    bridge = LocalAutonomyTelemetryBridgeV1()
    ev = bridge.derive(ledger, art, qual, escalation_count=10)
    assert ev.escalation_rate_signal is False


# ─────────────────────────────────────────────────────────────────────────────
# 5. EscalationWorkflowV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_escalation_event_local_executor_can_count():
    from framework.escalation_workflow_v1 import EscalationEventV1
    ev = EscalationEventV1(
        run_id="r1", package_id="P1",
        escalation_requested=False, escalation_reason="routine",
        escalation_approved=False, approver_type="auto",
        executor="aider", counts_as_local_autonomy_progress=True,
    )
    assert ev.counts_as_local_autonomy_progress is True


def test_escalation_event_claude_cannot_count():
    from framework.escalation_workflow_v1 import EscalationEventV1
    with pytest.raises(ValueError, match="counts_as_local_autonomy_progress must be False"):
        EscalationEventV1(
            run_id="r1", package_id="P1",
            escalation_requested=True, escalation_reason="rescue",
            escalation_approved=True, approver_type="human",
            executor="claude", counts_as_local_autonomy_progress=True,
        )


def test_escalation_workflow_records_event():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    wf = EscalationWorkflowV1()
    ev = wf.record_event("r1", "P1", False, "routine", False, "aider")
    assert ev.counts_as_local_autonomy_progress is True
    assert wf.escalated_count == 0
    assert wf.autonomy_progress_count == 1


def test_escalation_workflow_claude_auto_false():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    wf = EscalationWorkflowV1()
    ev = wf.record_event("r1", "P1", True, "rescue", True, "claude_code")
    assert ev.counts_as_local_autonomy_progress is False
    assert wf.escalated_count == 1


def test_escalation_workflow_evaluate_warranted():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    wf = EscalationWorkflowV1()
    decision = wf.evaluate(failure_count=3, retry_budget_remaining=0)
    assert decision.escalation_warranted is True
    assert len(decision.reasons) >= 1


def test_escalation_workflow_evaluate_not_warranted():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    wf = EscalationWorkflowV1()
    decision = wf.evaluate(failure_count=0, retry_budget_remaining=3)
    assert decision.escalation_warranted is False


def test_escalation_workflow_to_dict_fields():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    wf = EscalationWorkflowV1()
    wf.record_event("r1", "P1", False, "routine", False, "aider")
    d = wf.to_dict()
    for field in ("total_events", "escalated_count", "autonomy_progress_count", "events"):
        assert field in d, f"missing field: {field}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Phase6CloseoutRatifierV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_ratifier_inputs(pass_all=True, n_runs=3):
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    from framework.escalation_workflow_v1 import EscalationWorkflowV1

    # Use mkdtemp so directory outlives this function call
    tmp = tempfile.mkdtemp()
    ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "l.jsonl")
    for i in range(n_runs):
        ledger.append_record(
            run_id=f"r{i}", package_id="P1", package_label="S",
            executor="aider", route="local_fast",
            validation_results={"ok": pass_all},
        )

    art = UnifiedValidationArtifactV1.build(
        package_id="P1", package_label="S",
        validation_results={"a": True}, escalation_status="NOT_ESCALATED",
    )
    qual_ev = QualificationReadinessEvaluatorV1()
    qual = qual_ev.evaluate(True, 1.0, True)
    bridge = LocalAutonomyTelemetryBridgeV1()
    telemetry = bridge.derive(ledger, art, qual)

    wf = EscalationWorkflowV1()
    wf.record_event("r0", "P1", False, "routine", False, "aider")

    return ledger, telemetry, wf


def test_ratifier_closes_phase6_when_ready():
    from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutRatifierV1
    ledger, telemetry, wf = _make_ratifier_inputs(pass_all=True)
    ratifier = Phase6CloseoutRatifierV1()
    result = ratifier.ratify(ledger, telemetry, wf)
    assert result.phase6_closed is True
    assert result.blockers_remaining == []


def test_ratifier_not_closed_when_no_ledger_entries():
    from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutRatifierV1
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    from framework.local_autonomy_telemetry_bridge_v1 import LocalAutonomyTelemetryBridgeV1
    from framework.escalation_workflow_v1 import EscalationWorkflowV1

    with tempfile.TemporaryDirectory() as tmp:
        ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "l.jsonl")
        art = UnifiedValidationArtifactV1.build(
            package_id="P1", package_label="S",
            validation_results={"a": True}, escalation_status="NOT_ESCALATED",
        )
        qual_ev = QualificationReadinessEvaluatorV1()
        qual = qual_ev.evaluate(True, 1.0, True)
        bridge = LocalAutonomyTelemetryBridgeV1()
        telemetry = bridge.derive(ledger, art, qual)
        wf = EscalationWorkflowV1()

        ratifier = Phase6CloseoutRatifierV1()
        result = ratifier.ratify(ledger, telemetry, wf)
    assert result.phase6_closed is False


def test_ratifier_to_dict_fields():
    from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutRatifierV1
    ledger, telemetry, wf = _make_ratifier_inputs()
    ratifier = Phase6CloseoutRatifierV1()
    result = ratifier.ratify(ledger, telemetry, wf)
    d = result.to_dict()
    for field in ("phase6_closed", "blockers_remaining", "closeout_summary", "ratified_at"):
        assert field in d, f"missing field: {field}"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Phase7PromotionV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_promotion_inputs(phase6_closed=True, routine_ready=True):
    from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutResultV1
    from framework.local_autonomy_telemetry_bridge_v1 import TelemetryEvidenceSummaryV1
    from framework.regression_summary_v1 import RegressionSummaryV1, RegressionCaseV1

    closeout = Phase6CloseoutResultV1(
        phase6_closed=phase6_closed,
        blockers_remaining=[] if phase6_closed else ["P6-BLOCKER-03: not closed"],
        closeout_summary={"ledger_total_runs": 3},
    )
    telemetry = TelemetryEvidenceSummaryV1(
        routine_local_execution_ready=routine_ready,
        first_pass_success_signal=routine_ready,
        retry_discipline_signal=True,
        escalation_rate_signal=True,
        artifact_completeness_signal=routine_ready,
        evidence_gaps=[] if routine_ready else ["routine not ready"],
    )
    cases = [
        RegressionCaseV1(case_id=f"r{i}", task_class="bug_fix", passed=True)
        for i in range(4)
    ]
    regression = RegressionSummaryV1.from_cases(cases)
    return closeout, telemetry, regression


def test_promotion_ready_when_all_pass():
    from framework.phase7_promotion_v1 import Phase7PromotionV1
    closeout, telemetry, regression = _make_promotion_inputs(phase6_closed=True, routine_ready=True)
    promoter = Phase7PromotionV1()
    result = promoter.evaluate("P7-TEST", closeout, telemetry, regression)
    assert result.promotion_ready is True
    assert result.promotion_blockers == []


def test_promotion_blocked_when_phase6_not_closed():
    from framework.phase7_promotion_v1 import Phase7PromotionV1
    closeout, telemetry, regression = _make_promotion_inputs(phase6_closed=False)
    promoter = Phase7PromotionV1()
    result = promoter.evaluate("P7-TEST", closeout, telemetry, regression)
    assert result.promotion_ready is False
    assert any("phase6_not_closed" in b for b in result.promotion_blockers)


def test_promotion_blocked_when_not_routine_ready():
    from framework.phase7_promotion_v1 import Phase7PromotionV1
    closeout, telemetry, regression = _make_promotion_inputs(phase6_closed=True, routine_ready=False)
    promoter = Phase7PromotionV1()
    result = promoter.evaluate("P7-TEST", closeout, telemetry, regression)
    assert result.promotion_ready is False


def test_promotion_to_dict_fields():
    from framework.phase7_promotion_v1 import Phase7PromotionV1
    closeout, telemetry, regression = _make_promotion_inputs()
    promoter = Phase7PromotionV1()
    result = promoter.evaluate("P7-TEST", closeout, telemetry, regression)
    d = result.to_dict()
    for field in ("phase_id", "package_id", "promotion_ready", "promotion_blockers",
                  "promotion_summary", "generated_at"):
        assert field in d, f"missing field: {field}"


def test_promotion_phase_id_is_phase_7():
    from framework.phase7_promotion_v1 import Phase7PromotionV1
    closeout, telemetry, regression = _make_promotion_inputs()
    promoter = Phase7PromotionV1()
    result = promoter.evaluate("P7-TEST", closeout, telemetry, regression)
    assert result.phase_id == "phase_7"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Phase 7 baseline content seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_phase7_baseline():
    if not BASELINE_PATH.exists():
        pytest.skip("phase7_promotion_baseline.v1.yaml not found")
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


def test_phase7_baseline_phase_id():
    data = _load_phase7_baseline()
    assert data.get("phase_id") == "phase_7"


def test_phase7_baseline_required_modules():
    data = _load_phase7_baseline()
    rm = data.get("required_modules", {})
    required = [
        "persistent_execution_ledger_v1",
        "live_aider_dispatch_v1",
        "local_autonomy_telemetry_bridge_v1",
        "escalation_workflow_v1",
        "phase6_closeout_ratifier_v1",
        "phase7_promotion_v1",
    ]
    if isinstance(rm, dict):
        for name in required:
            assert name in rm, f"required_modules missing: {name}"
    else:
        pytest.skip("yaml unavailable; required_modules not fully parsed")


def test_phase7_baseline_has_required_capabilities():
    data = _load_phase7_baseline()
    assert "required_capabilities" in data


def test_phase7_baseline_has_completion_requirements():
    data = _load_phase7_baseline()
    assert "completion_requirements" in data


def test_phase7_baseline_has_remaining_blockers():
    data = _load_phase7_baseline()
    assert "remaining_blockers" in data


def test_phase7_baseline_has_promotion_gate():
    data = _load_phase7_baseline()
    assert "promotion_gate" in data


# ─────────────────────────────────────────────────────────────────────────────
# 9. Artifact structure seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_artifact():
    if not ARTIFACT_PATH.exists():
        pytest.skip("phase7_promotion_pack_check.json not yet emitted; run runner first")
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_artifact_phase7_pack_field():
    d = _load_artifact()
    assert d["phase7_pack"] == "live_local_first_promotion_v1"


def test_artifact_all_checks_passed():
    d = _load_artifact()
    assert d["all_checks_passed"] is True


def test_artifact_live_local_cases_run_gte_3():
    d = _load_artifact()
    assert d["live_local_cases_run"] >= 3


def test_artifact_escalation_accounting_checked():
    d = _load_artifact()
    assert d["escalation_accounting_checked"] is True


def test_artifact_phase6_closed_present():
    d = _load_artifact()
    assert "phase6_closed" in d
    assert isinstance(d["phase6_closed"], bool)


def test_artifact_promotion_ready_present():
    d = _load_artifact()
    assert "promotion_ready" in d
    assert isinstance(d["promotion_ready"], bool)


def test_artifact_promotion_blockers_present():
    d = _load_artifact()
    assert "promotion_blockers" in d
    assert isinstance(d["promotion_blockers"], list)


def test_artifact_escalation_status():
    d = _load_artifact()
    assert d.get("escalation_status") == "NOT_ESCALATED"


def test_artifact_component_summary_has_6_framework_modules():
    d = _load_artifact()
    cs = d.get("component_summary", [])
    framework_entries = [e for e in cs if "framework" in e.get("module", "")]
    assert len(framework_entries) >= 6


def test_artifact_required_modules_loaded():
    d = _load_artifact()
    assert d["required_modules_loaded"] is True


def test_artifact_generated_at_present():
    d = _load_artifact()
    assert "generated_at" in d and d["generated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# 10. Runner existence seams
# ─────────────────────────────────────────────────────────────────────────────

def test_runner_exists():
    runner = REPO_ROOT / "bin/run_phase7_promotion_pack_check.py"
    assert runner.exists()


def test_seam_test_file_exists():
    seam = REPO_ROOT / "tests/test_phase7_promotion_pack_seam.py"
    assert seam.exists()
