"""Seam tests for P6-01: Phase 6 Local-First Transition Pack."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase6_transition_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase6_local_first_transition_baseline.v1.yaml"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Import seams
# ─────────────────────────────────────────────────────────────────────────────

def test_import_local_execution_ledger_v1():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    assert LocalExecutionLedgerV1 is not None


def test_import_aider_execution_adapter_v1():
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    assert AiderExecutionAdapterV1 is not None


def test_import_local_autonomy_evidence_bridge_v1():
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    assert LocalAutonomyEvidenceBridgeV1 is not None


def test_import_escalation_record_v1():
    from framework.escalation_record_v1 import EscalationRecordV1
    assert EscalationRecordV1 is not None


def test_import_phase6_transition_v1():
    from framework.phase6_transition_v1 import Phase6TransitionV1
    assert Phase6TransitionV1 is not None


# ─────────────────────────────────────────────────────────────────────────────
# 2. LocalExecutionLedgerV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_ledger_records_run():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    ledger = LocalExecutionLedgerV1()
    entry = ledger.record(
        run_id="r001",
        package_id="PKG-001",
        package_label="SUBSTRATE",
        executor="aider",
        route="local_fast",
        validation_results={"make_check": True},
        escalation_status="NOT_ESCALATED",
    )
    assert entry.run_id == "r001"
    assert entry.executor == "aider"
    assert entry.final_outcome == "PASS"
    assert ledger.total_runs == 1


def test_ledger_pass_rate():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    ledger = LocalExecutionLedgerV1()
    ledger.record("r1", "P1", "SUBSTRATE", "aider", "local_fast", {"a": True})
    ledger.record("r2", "P2", "SUBSTRATE", "aider", "local_fast", {"a": False})
    assert ledger.pass_rate == 0.5
    assert ledger.passed_runs == 1


def test_ledger_to_dict_fields():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    ledger = LocalExecutionLedgerV1()
    ledger.record("r1", "P1", "SUBSTRATE", "aider", "local_fast", {"a": True})
    d = ledger.to_dict()
    for field in ("total_runs", "passed_runs", "pass_rate", "entries"):
        assert field in d, f"missing field: {field}"


def test_ledger_entry_to_dict_fields():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    ledger = LocalExecutionLedgerV1()
    entry = ledger.record("r1", "P1", "SUBSTRATE", "aider", "local_fast", {"a": True})
    d = entry.to_dict()
    for field in ("run_id", "package_id", "executor", "route", "validations_run",
                  "validation_results", "escalation_status", "final_outcome", "recorded_at"):
        assert field in d, f"missing field: {field}"


def test_ledger_multiple_entries():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    ledger = LocalExecutionLedgerV1()
    for i in range(4):
        ledger.record(f"r{i}", f"P{i}", "SUBSTRATE", "aider", "local_fast", {"ok": True})
    assert ledger.total_runs == 4
    assert len(ledger.all_entries()) == 4


# ─────────────────────────────────────────────────────────────────────────────
# 3. AiderExecutionAdapterV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_aider_adapter_build_handoff_ready():
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    adapter = AiderExecutionAdapterV1()
    record = adapter.build_handoff(
        package_id="PKG-001",
        allowed_files=["framework/some_v1.py"],
        task_class="bug_fix",
        difficulty="medium",
    )
    assert record.adapter_status == "ready"
    assert record.execution_mode == "local_first"
    assert record.package_id == "PKG-001"


def test_aider_adapter_blocked_when_no_files():
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    adapter = AiderExecutionAdapterV1()
    record = adapter.build_handoff(package_id="PKG-001", allowed_files=[])
    assert record.adapter_status == "blocked"


def test_aider_adapter_is_ready_true():
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    adapter = AiderExecutionAdapterV1()
    record = adapter.build_handoff(
        package_id="PKG-001",
        allowed_files=["framework/x.py"],
    )
    assert adapter.is_ready(record) is True


def test_aider_adapter_to_dict_fields():
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    adapter = AiderExecutionAdapterV1()
    record = adapter.build_handoff(
        package_id="PKG-001",
        allowed_files=["framework/x.py"],
    )
    d = record.to_dict()
    for field in ("package_id", "allowed_files", "validation_sequence",
                  "adapter_status", "execution_mode", "handoff_at"):
        assert field in d, f"missing field: {field}"


def test_aider_adapter_execution_mode_is_local_first():
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    adapter = AiderExecutionAdapterV1()
    record = adapter.build_handoff(package_id="PKG-001", allowed_files=["x.py"])
    assert record.execution_mode == "local_first"


# ─────────────────────────────────────────────────────────────────────────────
# 4. LocalAutonomyEvidenceBridgeV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_bridge_inputs(executor="aider", pass_rate_ok=True):
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1

    ledger = LocalExecutionLedgerV1()
    for i in range(3):
        ledger.record(
            run_id=f"r{i}", package_id="P1", package_label="SUBSTRATE",
            executor=executor, route="local_fast",
            validation_results={"a": pass_rate_ok},
        )

    art = UnifiedValidationArtifactV1.build(
        package_id="P1", package_label="SUBSTRATE",
        validation_results={"x": True}, escalation_status="NOT_ESCALATED",
    )

    qual_ev = QualificationReadinessEvaluatorV1()
    qual = qual_ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=1.0 if pass_rate_ok else 0.0,
        escalation_status_present=True,
    )
    return ledger, art, qual


def test_evidence_bridge_routine_ready_on_local_runs():
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    bridge = LocalAutonomyEvidenceBridgeV1()
    ledger, art, qual = _make_bridge_inputs(executor="aider")
    summary = bridge.derive(ledger, art, qual)
    assert summary.routine_local_execution_ready is True
    assert summary.claude_removed_from_routine_path_signal is True


def test_evidence_bridge_claude_signal_false_when_claude_in_ledger():
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    bridge = LocalAutonomyEvidenceBridgeV1()
    ledger, art, qual = _make_bridge_inputs(executor="claude_code")
    summary = bridge.derive(ledger, art, qual)
    assert summary.claude_removed_from_routine_path_signal is False


def test_evidence_bridge_explicit_escalation_required_always_true():
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    bridge = LocalAutonomyEvidenceBridgeV1()
    ledger, art, qual = _make_bridge_inputs(executor="aider")
    summary = bridge.derive(ledger, art, qual)
    assert summary.explicit_escalation_required is True


def test_evidence_bridge_to_dict_fields():
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    bridge = LocalAutonomyEvidenceBridgeV1()
    ledger, art, qual = _make_bridge_inputs()
    summary = bridge.derive(ledger, art, qual)
    d = summary.to_dict()
    for field in ("routine_local_execution_ready", "explicit_escalation_required",
                  "claude_removed_from_routine_path_signal", "evidence_gaps", "evidence_detail"):
        assert field in d, f"missing field: {field}"


def test_evidence_bridge_gaps_on_no_local_runs():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1

    ledger = LocalExecutionLedgerV1()  # empty
    art = UnifiedValidationArtifactV1.build(
        package_id="P1", package_label="SUBSTRATE",
        validation_results={"x": True}, escalation_status="NOT_ESCALATED",
    )
    qual_ev = QualificationReadinessEvaluatorV1()
    qual = qual_ev.evaluate(artifact_complete=True, validation_pass_rate=1.0,
                            escalation_status_present=True)
    bridge = LocalAutonomyEvidenceBridgeV1()
    summary = bridge.derive(ledger, art, qual)
    assert summary.routine_local_execution_ready is False
    assert len(summary.evidence_gaps) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. EscalationRecordV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_escalation_record_local_executor_can_count_as_progress():
    from framework.escalation_record_v1 import EscalationRecordV1
    rec = EscalationRecordV1(
        run_id="r1", package_id="P1",
        escalation_requested=False, escalation_approved=False,
        escalation_reason="routine_run",
        counts_as_local_autonomy_progress=True,
        executor="aider",
    )
    assert rec.counts_as_local_autonomy_progress is True


def test_escalation_record_claude_executor_cannot_count_as_progress():
    from framework.escalation_record_v1 import EscalationRecordV1
    with pytest.raises(ValueError, match="counts_as_local_autonomy_progress must be False"):
        EscalationRecordV1(
            run_id="r1", package_id="P1",
            escalation_requested=True, escalation_approved=True,
            escalation_reason="claude_rescue",
            counts_as_local_autonomy_progress=True,
            executor="claude",
        )


def test_escalation_record_claude_code_enforces_invariant():
    from framework.escalation_record_v1 import EscalationRecordV1
    with pytest.raises(ValueError):
        EscalationRecordV1(
            run_id="r2", package_id="P1",
            escalation_requested=True, escalation_approved=True,
            escalation_reason="rescue",
            counts_as_local_autonomy_progress=True,
            executor="claude_code",
        )


def test_escalation_record_to_dict_fields():
    from framework.escalation_record_v1 import EscalationRecordV1
    rec = EscalationRecordV1(
        run_id="r1", package_id="P1",
        escalation_requested=False, escalation_approved=False,
        escalation_reason="routine",
        counts_as_local_autonomy_progress=True,
        executor="aider",
    )
    d = rec.to_dict()
    for field in ("run_id", "package_id", "escalation_requested", "escalation_approved",
                  "escalation_reason", "counts_as_local_autonomy_progress", "executor"):
        assert field in d, f"missing field: {field}"


def test_escalation_registry_auto_sets_counts_false_for_claude():
    from framework.escalation_record_v1 import EscalationRegistryV1
    registry = EscalationRegistryV1()
    rec = registry.record(
        run_id="r1", package_id="P1",
        escalation_requested=True, escalation_approved=True,
        escalation_reason="rescue",
        executor="claude",
    )
    assert rec.counts_as_local_autonomy_progress is False


def test_escalation_registry_auto_sets_counts_true_for_aider():
    from framework.escalation_record_v1 import EscalationRegistryV1
    registry = EscalationRegistryV1()
    rec = registry.record(
        run_id="r1", package_id="P1",
        escalation_requested=False, escalation_approved=False,
        escalation_reason="routine",
        executor="aider",
    )
    assert rec.counts_as_local_autonomy_progress is True


def test_escalation_registry_to_dict_fields():
    from framework.escalation_record_v1 import EscalationRegistryV1
    registry = EscalationRegistryV1()
    registry.record("r1", "P1", False, False, "routine", "aider")
    d = registry.to_dict()
    for field in ("total_records", "escalated_count", "autonomy_progress_count", "records"):
        assert field in d, f"missing field: {field}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Phase6TransitionV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_transition_inputs():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    from framework.escalation_record_v1 import EscalationRegistryV1

    ledger = LocalExecutionLedgerV1()
    for i in range(3):
        ledger.record(f"r{i}", "P1", "SUBSTRATE", "aider", "local_fast", {"ok": True})

    adapter = AiderExecutionAdapterV1()
    handoff = adapter.build_handoff("P6-TEST", allowed_files=["framework/x.py"])

    art = UnifiedValidationArtifactV1.build(
        package_id="P6-TEST", package_label="SUBSTRATE",
        validation_results={"a": True}, escalation_status="NOT_ESCALATED",
    )
    qual_ev = QualificationReadinessEvaluatorV1()
    qual = qual_ev.evaluate(artifact_complete=True, validation_pass_rate=1.0,
                            escalation_status_present=True)
    bridge = LocalAutonomyEvidenceBridgeV1()
    evidence = bridge.derive(ledger, art, qual)

    registry = EscalationRegistryV1()
    registry.record("r0", "P1", False, False, "routine", "aider")

    return ledger, handoff, evidence, registry


def test_transition_assemble_returns_result():
    from framework.phase6_transition_v1 import Phase6TransitionV1
    ledger, handoff, evidence, registry = _make_transition_inputs()
    t = Phase6TransitionV1()
    result = t.assemble("P6-TEST", ledger, handoff, evidence, registry)
    assert result is not None
    assert result.phase_id == "phase_6"


def test_transition_ready_when_all_pass():
    from framework.phase6_transition_v1 import Phase6TransitionV1
    ledger, handoff, evidence, registry = _make_transition_inputs()
    t = Phase6TransitionV1()
    result = t.assemble("P6-TEST", ledger, handoff, evidence, registry)
    assert result.transition_ready is True


def test_transition_to_dict_fields():
    from framework.phase6_transition_v1 import Phase6TransitionV1
    ledger, handoff, evidence, registry = _make_transition_inputs()
    t = Phase6TransitionV1()
    result = t.assemble("P6-TEST", ledger, handoff, evidence, registry)
    d = result.to_dict()
    for field in ("phase_id", "package_id", "generated_at", "ledger_summary",
                  "aider_handoff", "autonomy_evidence", "escalation_registry_summary",
                  "escalation_status", "transition_ready", "closing_notes"):
        assert field in d, f"missing field: {field}"


def test_transition_escalation_status_present():
    from framework.phase6_transition_v1 import Phase6TransitionV1
    ledger, handoff, evidence, registry = _make_transition_inputs()
    t = Phase6TransitionV1()
    result = t.assemble("P6-TEST", ledger, handoff, evidence, registry,
                        escalation_status="NOT_ESCALATED")
    assert result.escalation_status == "NOT_ESCALATED"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Phase 6 baseline content seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_phase6_baseline():
    if not BASELINE_PATH.exists():
        pytest.skip("phase6_local_first_transition_baseline.v1.yaml not found")
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


def test_phase6_baseline_phase_id():
    data = _load_phase6_baseline()
    assert data.get("phase_id") == "phase_6"


def test_phase6_baseline_required_modules():
    data = _load_phase6_baseline()
    rm = data.get("required_modules", {})
    required = [
        "local_execution_ledger_v1",
        "aider_execution_adapter_v1",
        "local_autonomy_evidence_bridge_v1",
        "escalation_record_v1",
        "phase6_transition_v1",
    ]
    if isinstance(rm, dict):
        for name in required:
            assert name in rm, f"required_modules missing: {name}"
    else:
        pytest.skip("yaml not available; required_modules not fully parsed")


def test_phase6_baseline_has_required_capabilities():
    data = _load_phase6_baseline()
    assert "required_capabilities" in data


def test_phase6_baseline_has_completion_requirements():
    data = _load_phase6_baseline()
    assert "completion_requirements" in data


def test_phase6_baseline_has_remaining_blockers():
    data = _load_phase6_baseline()
    assert "remaining_blockers" in data


def test_phase6_baseline_has_transition_gate():
    data = _load_phase6_baseline()
    assert "transition_gate" in data


# ─────────────────────────────────────────────────────────────────────────────
# 8. Artifact structure seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_artifact():
    if not ARTIFACT_PATH.exists():
        pytest.skip("phase6_transition_pack_check.json not yet emitted; run the runner first")
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_artifact_phase6_pack_field():
    d = _load_artifact()
    assert d["phase6_pack"] == "local_first_transition_v1"


def test_artifact_all_checks_passed():
    d = _load_artifact()
    assert d["all_checks_passed"] is True


def test_artifact_local_execution_cases_run_gte_3():
    d = _load_artifact()
    assert d["local_execution_cases_run"] >= 3


def test_artifact_escalation_accounting_checked():
    d = _load_artifact()
    assert d["escalation_accounting_checked"] is True


def test_artifact_routine_local_execution_ready_present():
    d = _load_artifact()
    assert "routine_local_execution_ready" in d
    assert isinstance(d["routine_local_execution_ready"], bool)


def test_artifact_claude_removed_signal_present():
    d = _load_artifact()
    assert "claude_removed_from_routine_path_signal" in d
    assert isinstance(d["claude_removed_from_routine_path_signal"], bool)


def test_artifact_escalation_status():
    d = _load_artifact()
    assert d.get("escalation_status") == "NOT_ESCALATED"


def test_artifact_component_summary_has_5_framework_modules():
    d = _load_artifact()
    cs = d.get("component_summary", [])
    framework_entries = [e for e in cs if "framework" in e.get("module", "")]
    assert len(framework_entries) >= 5


def test_artifact_required_modules_loaded():
    d = _load_artifact()
    assert d["required_modules_loaded"] is True


def test_artifact_generated_at_present():
    d = _load_artifact()
    assert "generated_at" in d and d["generated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# 9. Runner existence seams
# ─────────────────────────────────────────────────────────────────────────────

def test_runner_exists():
    runner = REPO_ROOT / "bin/run_phase6_transition_pack_check.py"
    assert runner.exists()


def test_seam_test_file_exists():
    seam = REPO_ROOT / "tests/test_phase6_transition_pack_seam.py"
    assert seam.exists()
