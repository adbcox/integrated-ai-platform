"""Seam tests for P7-02: Phase 7 Live Evidence Closeout Pack."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase7_live_evidence_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase7_terminal_closeout.v1.yaml"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Import seams
# ─────────────────────────────────────────────────────────────────────────────

def test_import_live_aider_proof_v1():
    from framework.live_aider_proof_v1 import LiveAiderProofV1
    assert LiveAiderProofV1 is not None


def test_import_real_telemetry_ingestion_v1():
    from framework.real_telemetry_ingestion_v1 import RealTelemetryIngestionV1
    assert RealTelemetryIngestionV1 is not None


def test_import_live_escalation_evidence_v1():
    from framework.live_escalation_evidence_v1 import LiveEscalationEvidenceV1
    assert LiveEscalationEvidenceV1 is not None


def test_import_promotion_gate_ratifier_v1():
    from framework.promotion_gate_ratifier_v1 import PromotionGateRatifierV1
    assert PromotionGateRatifierV1 is not None


def test_import_phase7_terminal_closeout_v1():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    assert Phase7TerminalCloseoutV1 is not None


# ─────────────────────────────────────────────────────────────────────────────
# 2. LiveAiderProofV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_aider_proof_dry_run_returns_result():
    from framework.live_aider_proof_v1 import LiveAiderProofV1, PROOF_MODE_DRY_RUN_ONLY
    proof = LiveAiderProofV1()
    result = proof.prove(
        package_id="P7-TEST",
        allowed_files=["framework/x.py"],
        message="test message",
        attempt_live=False,
    )
    assert result.live_dispatch_attempted is False
    assert result.live_dispatch_succeeded is False
    assert result.dispatch_mode == PROOF_MODE_DRY_RUN_ONLY


def test_aider_proof_attempt_live_when_not_installed():
    from framework.live_aider_proof_v1 import LiveAiderProofV1
    proof = LiveAiderProofV1()
    result = proof.prove(
        package_id="P7-TEST",
        allowed_files=["framework/x.py"],
        message="test",
        attempt_live=True,
    )
    # Either succeeded (aider installed) or truthfully fell back
    assert result.live_dispatch_attempted is True
    if not result.live_dispatch_succeeded:
        assert result.dispatch_mode in ("dry_run_only", "blocked")
        assert result.failure_reason is not None


def test_aider_proof_no_false_live_claim():
    from framework.live_aider_proof_v1 import LiveAiderProofV1, PROOF_MODE_LIVE
    proof = LiveAiderProofV1()
    result = proof.prove(
        package_id="P7-TEST",
        allowed_files=["framework/x.py"],
        message="test",
        attempt_live=False,
    )
    # dry-run mode must not claim live
    assert result.dispatch_mode != PROOF_MODE_LIVE


def test_aider_proof_to_dict_fields():
    from framework.live_aider_proof_v1 import LiveAiderProofV1
    proof = LiveAiderProofV1()
    result = proof.prove(
        package_id="P7-TEST", allowed_files=["x.py"], message="m", attempt_live=False
    )
    d = result.to_dict()
    for field in ("live_dispatch_attempted", "live_dispatch_succeeded", "dispatch_mode",
                  "failure_reason", "dispatch_record", "proved_at", "notes"):
        assert field in d, f"missing field: {field}"


def test_aider_proof_blocked_when_no_files():
    from framework.live_aider_proof_v1 import LiveAiderProofV1
    proof = LiveAiderProofV1()
    result = proof.prove(
        package_id="P7-TEST", allowed_files=[], message="m", attempt_live=True
    )
    assert result.live_dispatch_succeeded is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. RealTelemetryIngestionV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_ledger_with_entries(n=3):
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    tmp = tempfile.mkdtemp()
    ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "l.jsonl")
    for i in range(n):
        ledger.append_record(
            run_id=f"live-run-{i:03d}",
            package_id="P7-TEST",
            package_label="SUBSTRATE",
            executor="aider",
            route="local_fast",
            validation_results={"ok": True},
        )
    return ledger


def test_telemetry_ingestion_reads_ledger():
    from framework.real_telemetry_ingestion_v1 import RealTelemetryIngestionV1
    ledger = _make_ledger_with_entries(3)
    ingestion = RealTelemetryIngestionV1()
    result = ingestion.ingest(ledger=ledger)
    assert result.ledger_entries_seen == 3


def test_telemetry_ingestion_complete_with_artifacts():
    from framework.real_telemetry_ingestion_v1 import RealTelemetryIngestionV1
    ledger = _make_ledger_with_entries(3)
    ingestion = RealTelemetryIngestionV1()
    result = ingestion.ingest(ledger=ledger, repo_root=REPO_ROOT)
    # real_artifacts_seen >= 1 because prior packages produced artifacts
    assert result.real_artifacts_seen >= 1
    assert result.telemetry_complete is True


def test_telemetry_ingestion_incomplete_when_no_ledger():
    from framework.real_telemetry_ingestion_v1 import RealTelemetryIngestionV1
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    tmp = tempfile.mkdtemp()
    empty_ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "empty.jsonl")
    ingestion = RealTelemetryIngestionV1()
    result = ingestion.ingest(ledger=empty_ledger)
    assert result.ledger_entries_seen == 0
    assert result.telemetry_complete is False


def test_telemetry_ingestion_to_dict_fields():
    from framework.real_telemetry_ingestion_v1 import RealTelemetryIngestionV1
    ledger = _make_ledger_with_entries(2)
    ingestion = RealTelemetryIngestionV1()
    result = ingestion.ingest(ledger=ledger)
    d = result.to_dict()
    for field in ("ledger_entries_seen", "real_artifacts_seen", "synthetic_only",
                  "telemetry_complete", "evidence_gaps", "ingested_at", "detail"):
        assert field in d, f"missing field: {field}"


def test_telemetry_ingestion_evidence_gaps_on_no_artifacts():
    from framework.real_telemetry_ingestion_v1 import RealTelemetryIngestionV1
    from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
    tmp = tempfile.mkdtemp()
    empty_ledger = PersistentExecutionLedgerV1(ledger_path=Path(tmp) / "empty.jsonl")
    ingestion = RealTelemetryIngestionV1()
    result = ingestion.ingest(ledger=empty_ledger, repo_root=Path(tmp))
    assert len(result.evidence_gaps) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 4. LiveEscalationEvidenceV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def test_escalation_evidence_local_executor_preserves_autonomy():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    from framework.live_escalation_evidence_v1 import LiveEscalationEvidenceV1

    wf = EscalationWorkflowV1()
    for i in range(3):
        wf.record_event(f"r{i}", "P1", False, "routine", False, "aider")

    ev = LiveEscalationEvidenceV1()
    summary = ev.derive(wf)
    assert summary.local_autonomy_progress_preserved is True
    assert summary.escalation_events_seen == 3
    assert summary.remote_assist_events == 0


def test_escalation_evidence_claude_not_counted_as_progress():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    from framework.live_escalation_evidence_v1 import LiveEscalationEvidenceV1

    wf = EscalationWorkflowV1()
    wf.record_event("r1", "P1", True, "rescue", True, "claude_code")

    ev = LiveEscalationEvidenceV1()
    summary = ev.derive(wf)
    assert summary.remote_assist_events == 1
    # Invariant preserved — registry sets counts=False automatically
    assert summary.local_autonomy_progress_preserved is True


def test_escalation_evidence_to_dict_fields():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    from framework.live_escalation_evidence_v1 import LiveEscalationEvidenceV1

    wf = EscalationWorkflowV1()
    wf.record_event("r1", "P1", False, "routine", False, "aider")
    ev = LiveEscalationEvidenceV1()
    summary = ev.derive(wf)
    d = summary.to_dict()
    for field in ("escalation_events_seen", "escalation_required_events", "remote_assist_events",
                  "local_autonomy_progress_preserved", "evidence_gaps", "recorded_at", "detail"):
        assert field in d, f"missing field: {field}"


def test_escalation_evidence_gap_on_no_events():
    from framework.escalation_workflow_v1 import EscalationWorkflowV1
    from framework.live_escalation_evidence_v1 import LiveEscalationEvidenceV1

    wf = EscalationWorkflowV1()
    ev = LiveEscalationEvidenceV1()
    summary = ev.derive(wf)
    assert len(summary.evidence_gaps) > 0
    assert summary.escalation_events_seen == 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. PromotionGateRatifierV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_gate_inputs(live_succeeded=False, telem_complete=True, autonomy_ok=True, promo_ready=True):
    from framework.live_aider_proof_v1 import AiderProofResultV1, PROOF_MODE_DRY_RUN_ONLY, PROOF_MODE_LIVE
    from framework.real_telemetry_ingestion_v1 import TelemetryIngestionResultV1
    from framework.live_escalation_evidence_v1 import EscalationEvidenceSummaryV1
    from framework.phase7_promotion_v1 import Phase7PromotionResultV1

    aider_proof = AiderProofResultV1(
        live_dispatch_attempted=live_succeeded,
        live_dispatch_succeeded=live_succeeded,
        dispatch_mode=PROOF_MODE_LIVE if live_succeeded else PROOF_MODE_DRY_RUN_ONLY,
        failure_reason=None if live_succeeded else "aider not found on PATH; live dispatch unavailable",
        dispatch_record=None,
    )
    telemetry = TelemetryIngestionResultV1(
        ledger_entries_seen=4 if telem_complete else 0,
        real_artifacts_seen=3 if telem_complete else 0,
        synthetic_only=False,
        telemetry_complete=telem_complete,
        evidence_gaps=[] if telem_complete else ["no ledger entries"],
    )
    escalation = EscalationEvidenceSummaryV1(
        escalation_events_seen=4,
        escalation_required_events=0,
        remote_assist_events=0,
        local_autonomy_progress_preserved=autonomy_ok,
        evidence_gaps=[] if autonomy_ok else ["violation"],
    )
    promotion = Phase7PromotionResultV1(
        phase_id="phase_7",
        package_id="P7-TEST",
        promotion_ready=promo_ready,
        promotion_blockers=[] if promo_ready else ["not ready"],
        promotion_summary={},
    )
    return aider_proof, telemetry, escalation, promotion


def test_gate_cleared_when_all_pass():
    from framework.promotion_gate_ratifier_v1 import PromotionGateRatifierV1
    aider, telem, esc, promo = _make_gate_inputs(
        live_succeeded=True, telem_complete=True, autonomy_ok=True, promo_ready=True
    )
    ratifier = PromotionGateRatifierV1()
    result = ratifier.ratify(aider, telem, esc, promo)
    assert result.promotion_gate_cleared is True
    assert result.blockers_remaining == []


def test_gate_blocked_when_live_not_attempted():
    from framework.promotion_gate_ratifier_v1 import PromotionGateRatifierV1
    aider, telem, esc, promo = _make_gate_inputs(live_succeeded=False)
    ratifier = PromotionGateRatifierV1()
    result = ratifier.ratify(aider, telem, esc, promo)
    assert result.promotion_gate_cleared is False
    assert any("aider_proof" in b for b in result.blockers_remaining)


def test_gate_blocked_when_telemetry_incomplete():
    from framework.promotion_gate_ratifier_v1 import PromotionGateRatifierV1
    aider, telem, esc, promo = _make_gate_inputs(live_succeeded=True, telem_complete=False)
    ratifier = PromotionGateRatifierV1()
    result = ratifier.ratify(aider, telem, esc, promo)
    assert result.promotion_gate_cleared is False
    assert any("telemetry" in b for b in result.blockers_remaining)


def test_gate_to_dict_fields():
    from framework.promotion_gate_ratifier_v1 import PromotionGateRatifierV1
    aider, telem, esc, promo = _make_gate_inputs()
    ratifier = PromotionGateRatifierV1()
    result = ratifier.ratify(aider, telem, esc, promo)
    d = result.to_dict()
    for field in ("promotion_gate_cleared", "blockers_remaining", "readiness_summary", "ratified_at"):
        assert field in d, f"missing field: {field}"


def test_gate_readiness_summary_fields():
    from framework.promotion_gate_ratifier_v1 import PromotionGateRatifierV1
    aider, telem, esc, promo = _make_gate_inputs(live_succeeded=True, telem_complete=True)
    ratifier = PromotionGateRatifierV1()
    result = ratifier.ratify(aider, telem, esc, promo)
    summary = result.readiness_summary
    for key in ("aider_proof_dispatch_mode", "aider_live_succeeded", "telemetry_complete",
                "local_autonomy_preserved", "promotion_ready"):
        assert key in summary, f"missing readiness_summary key: {key}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Phase7TerminalCloseoutV1 seams
# ─────────────────────────────────────────────────────────────────────────────

def _make_terminal_inputs(phase6_closed=True, promo_ready=True, gate_cleared=True, telem_complete=True):
    from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutResultV1
    from framework.phase7_promotion_v1 import Phase7PromotionResultV1
    from framework.promotion_gate_ratifier_v1 import PromotionGateResultV1
    from framework.real_telemetry_ingestion_v1 import TelemetryIngestionResultV1

    closeout = Phase6CloseoutResultV1(
        phase6_closed=phase6_closed,
        blockers_remaining=[] if phase6_closed else ["P6-BLOCKER-03"],
        closeout_summary={},
    )
    promotion = Phase7PromotionResultV1(
        phase_id="phase_7", package_id="P7-TEST",
        promotion_ready=promo_ready,
        promotion_blockers=[] if promo_ready else ["not ready"],
        promotion_summary={},
    )
    gate = PromotionGateResultV1(
        promotion_gate_cleared=gate_cleared,
        blockers_remaining=[] if gate_cleared else ["aider_proof: dry_run_only"],
        readiness_summary={},
    )
    telem = TelemetryIngestionResultV1(
        ledger_entries_seen=4 if telem_complete else 0,
        real_artifacts_seen=3 if telem_complete else 0,
        synthetic_only=False,
        telemetry_complete=telem_complete,
        evidence_gaps=[],
    )
    return closeout, promotion, gate, telem


def test_terminal_closeout_ready_when_all_pass():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    closeout, promotion, gate, telem = _make_terminal_inputs(
        phase6_closed=True, promo_ready=True, gate_cleared=True, telem_complete=True
    )
    t = Phase7TerminalCloseoutV1()
    result = t.assemble("P7-TEST", closeout, promotion, gate, telem)
    assert result.terminal_closeout_ready is True
    assert result.phase6_closed is True
    assert result.promotion_gate_cleared is True


def test_terminal_not_ready_when_phase6_not_closed():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    closeout, promotion, gate, telem = _make_terminal_inputs(phase6_closed=False)
    t = Phase7TerminalCloseoutV1()
    result = t.assemble("P7-TEST", closeout, promotion, gate, telem)
    assert result.terminal_closeout_ready is False


def test_terminal_not_ready_when_gate_not_cleared():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    closeout, promotion, gate, telem = _make_terminal_inputs(gate_cleared=False)
    t = Phase7TerminalCloseoutV1()
    result = t.assemble("P7-TEST", closeout, promotion, gate, telem)
    assert result.terminal_closeout_ready is False
    assert len(result.blockers_remaining) > 0


def test_terminal_to_dict_fields():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    closeout, promotion, gate, telem = _make_terminal_inputs()
    t = Phase7TerminalCloseoutV1()
    result = t.assemble("P7-TEST", closeout, promotion, gate, telem)
    d = result.to_dict()
    for field in ("phase_id", "package_id", "phase6_closed", "promotion_ready",
                  "promotion_gate_cleared", "terminal_closeout_ready", "blockers_remaining",
                  "terminal_summary", "escalation_status", "generated_at"):
        assert field in d, f"missing field: {field}"


def test_terminal_phase_id_is_phase_7():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    closeout, promotion, gate, telem = _make_terminal_inputs()
    t = Phase7TerminalCloseoutV1()
    result = t.assemble("P7-TEST", closeout, promotion, gate, telem)
    assert result.phase_id == "phase_7"


def test_terminal_escalation_status_present():
    from framework.phase7_terminal_closeout_v1 import Phase7TerminalCloseoutV1
    closeout, promotion, gate, telem = _make_terminal_inputs()
    t = Phase7TerminalCloseoutV1()
    result = t.assemble("P7-TEST", closeout, promotion, gate, telem,
                        escalation_status="NOT_ESCALATED")
    assert result.escalation_status == "NOT_ESCALATED"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Phase 7 terminal baseline content seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_terminal_baseline():
    if not BASELINE_PATH.exists():
        pytest.skip("phase7_terminal_closeout.v1.yaml not found")
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


def test_terminal_baseline_phase_id():
    data = _load_terminal_baseline()
    assert data.get("phase_id") == "phase_7"


def test_terminal_baseline_required_modules():
    data = _load_terminal_baseline()
    rm = data.get("required_modules", {})
    required = [
        "live_aider_proof_v1",
        "real_telemetry_ingestion_v1",
        "live_escalation_evidence_v1",
        "promotion_gate_ratifier_v1",
        "phase7_terminal_closeout_v1",
    ]
    if isinstance(rm, dict):
        for name in required:
            assert name in rm, f"required_modules missing: {name}"
    else:
        pytest.skip("yaml unavailable; required_modules not fully parsed")


def test_terminal_baseline_has_required_live_evidence():
    data = _load_terminal_baseline()
    assert "required_live_evidence" in data


def test_terminal_baseline_has_completion_requirements():
    data = _load_terminal_baseline()
    assert "completion_requirements" in data


def test_terminal_baseline_has_remaining_blockers():
    data = _load_terminal_baseline()
    assert "remaining_blockers" in data


def test_terminal_baseline_has_terminal_gate():
    data = _load_terminal_baseline()
    assert "terminal_gate" in data


# ─────────────────────────────────────────────────────────────────────────────
# 8. Artifact structure seams
# ─────────────────────────────────────────────────────────────────────────────

def _load_artifact():
    if not ARTIFACT_PATH.exists():
        pytest.skip("phase7_live_evidence_pack_check.json not yet emitted; run runner first")
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_artifact_phase7_live_pack_field():
    d = _load_artifact()
    assert d["phase7_live_pack"] == "live_evidence_closeout_v1"


def test_artifact_all_checks_passed():
    d = _load_artifact()
    assert d["all_checks_passed"] is True


def test_artifact_promotion_gate_cleared_present():
    d = _load_artifact()
    assert "promotion_gate_cleared" in d
    assert isinstance(d["promotion_gate_cleared"], bool)


def test_artifact_blockers_remaining_present():
    d = _load_artifact()
    assert "blockers_remaining" in d
    assert isinstance(d["blockers_remaining"], list)


def test_artifact_terminal_closeout_ready_present():
    d = _load_artifact()
    assert "terminal_closeout_ready" in d
    assert isinstance(d["terminal_closeout_ready"], bool)


def test_artifact_live_dispatch_fields_present():
    d = _load_artifact()
    assert "live_dispatch_attempted" in d
    assert "live_dispatch_succeeded" in d


def test_artifact_telemetry_complete_present():
    d = _load_artifact()
    assert "telemetry_complete" in d
    assert isinstance(d["telemetry_complete"], bool)


def test_artifact_escalation_accounting_checked():
    d = _load_artifact()
    assert d["escalation_accounting_checked"] is True


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
    runner = REPO_ROOT / "bin/run_phase7_live_evidence_pack_check.py"
    assert runner.exists()


def test_seam_test_file_exists():
    seam = REPO_ROOT / "tests/test_phase7_live_evidence_pack_seam.py"
    assert seam.exists()
