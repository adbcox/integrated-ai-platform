"""Seam tests for P7-03: FinalPromotionRatifierV1 evidence-chain ratification."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ── import seams ──────────────────────────────────────────────────────────────

def test_import_final_promotion_ratifier_v1():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    assert FinalPromotionRatifierV1 is not None


def test_import_final_ratification_result_v1():
    from framework.final_promotion_ratifier_v1 import FinalRatificationResultV1
    assert FinalRatificationResultV1 is not None


def test_ratifier_instantiation():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1()
    assert r is not None


def test_ratifier_instantiation_with_repo_root():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    assert r is not None


def test_result_dataclass_fields():
    from framework.final_promotion_ratifier_v1 import FinalRatificationResultV1
    r = FinalRatificationResultV1(
        phase7_final_ratified=False,
        promotion_gate_cleared=False,
        remaining_blockers=["blocker-x"],
        live_evidence_seen=False,
        final_summary={},
    )
    assert r.phase7_final_ratified is False
    assert r.promotion_gate_cleared is False
    assert r.remaining_blockers == ["blocker-x"]
    assert r.live_evidence_seen is False
    assert isinstance(r.ratified_at, str)


def test_result_to_dict():
    from framework.final_promotion_ratifier_v1 import FinalRatificationResultV1
    r = FinalRatificationResultV1(
        phase7_final_ratified=True,
        promotion_gate_cleared=True,
        remaining_blockers=[],
        live_evidence_seen=True,
        final_summary={"total_blockers": 0},
    )
    d = r.to_dict()
    assert d["phase7_final_ratified"] is True
    assert d["promotion_gate_cleared"] is True
    assert d["remaining_blockers"] == []
    assert d["live_evidence_seen"] is True
    assert "ratified_at" in d


# ── no-evidence seams (empty directory) ──────────────────────────────────────

def _make_ratifier(tmp_dir: str) -> "FinalPromotionRatifierV1":
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    return FinalPromotionRatifierV1(repo_root=Path(tmp_dir))


def test_ratify_returns_result_when_no_evidence():
    from framework.final_promotion_ratifier_v1 import FinalRatificationResultV1
    tmp = tempfile.mkdtemp()
    ratifier = _make_ratifier(tmp)
    result = ratifier.ratify()
    assert isinstance(result, FinalRatificationResultV1)


def test_ratify_blocked_when_no_evidence():
    tmp = tempfile.mkdtemp()
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    assert result.promotion_gate_cleared is False


def test_ratify_has_blockers_when_no_evidence():
    tmp = tempfile.mkdtemp()
    result = _make_ratifier(tmp).ratify()
    assert len(result.remaining_blockers) > 0


def test_ratify_load_errors_when_required_files_absent():
    tmp = tempfile.mkdtemp()
    result = _make_ratifier(tmp).ratify()
    load_errors = result.final_summary.get("load_errors", [])
    assert len(load_errors) >= 2  # at least promotion_pack + live_evidence


def test_ratify_live_evidence_not_seen_when_absent():
    tmp = tempfile.mkdtemp()
    result = _make_ratifier(tmp).ratify()
    assert result.live_evidence_seen is False


def test_ratify_final_summary_present():
    tmp = tempfile.mkdtemp()
    result = _make_ratifier(tmp).ratify()
    assert isinstance(result.final_summary, dict)
    assert "total_blockers" in result.final_summary


# ── helpers for writing evidence files ───────────────────────────────────────

def _write_promotion_pack(root: str, all_checks_passed=True, promotion_ready=True,
                           blockers=None) -> None:
    p = Path(root) / "artifacts" / "substrate"
    p.mkdir(parents=True, exist_ok=True)
    (p / "phase7_promotion_pack_check.json").write_text(json.dumps({
        "all_checks_passed": all_checks_passed,
        "promotion_ready": promotion_ready,
        "promotion_blockers": blockers or [],
    }), encoding="utf-8")


def _write_live_evidence(root: str, all_checks=True, telemetry=True,
                          dispatch_succeeded=False, mode="dry_run_only",
                          autonomy_preserved=True) -> None:
    p = Path(root) / "artifacts" / "substrate"
    p.mkdir(parents=True, exist_ok=True)
    (p / "phase7_live_evidence_pack_check.json").write_text(json.dumps({
        "all_checks_passed": all_checks,
        "telemetry_complete": telemetry,
        "live_dispatch_succeeded": dispatch_succeeded,
        "dispatch_mode": mode,
        "local_autonomy_progress_preserved": autonomy_preserved,
    }), encoding="utf-8")


def _write_live_proof_chain(root: str, dispatch_succeeded=True) -> None:
    p = Path(root) / "artifacts" / "local_runs"
    p.mkdir(parents=True, exist_ok=True)
    (p / "local_live_proof_chain.json").write_text(json.dumps({
        "live_dispatch_succeeded": dispatch_succeeded,
        "dispatch_mode": "live" if dispatch_succeeded else "dry_run_only",
    }), encoding="utf-8")


# ── partial evidence: promotion pack only ────────────────────────────────────

def test_ratify_blocked_with_promotion_pack_only():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False


def test_ratify_live_evidence_not_seen_with_pack_only():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    result = _make_ratifier(tmp).ratify()
    assert result.live_evidence_seen is False


def test_ratify_blocked_when_pack_fails():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp, all_checks_passed=False)
    _write_live_evidence(tmp)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    blockers_text = " ".join(result.remaining_blockers)
    assert "all_checks_passed" in blockers_text


def test_ratify_blocked_when_promotion_not_ready():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp, promotion_ready=False, blockers=["some-blocker"])
    _write_live_evidence(tmp)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    blockers_text = " ".join(result.remaining_blockers)
    assert "promotion_ready" in blockers_text


# ── partial evidence: both packs but dispatch dry-run ────────────────────────

def test_ratify_live_evidence_seen_when_pack_loaded():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp)
    result = _make_ratifier(tmp).ratify()
    assert result.live_evidence_seen is True


def test_ratify_blocked_when_dispatch_dry_run():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    assert result.promotion_gate_cleared is False


def test_ratify_dispatch_blocker_present_in_dry_run():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    result = _make_ratifier(tmp).ratify()
    blockers_text = " ".join(result.remaining_blockers)
    assert "live_dispatch_succeeded=False" in blockers_text


def test_ratify_dispatch_mode_in_blocker_message():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    result = _make_ratifier(tmp).ratify()
    blockers_text = " ".join(result.remaining_blockers)
    assert "dry_run_only" in blockers_text


def test_ratify_single_blocker_in_dry_run_state():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    result = _make_ratifier(tmp).ratify()
    assert len(result.remaining_blockers) == 1


def test_ratify_blocked_when_telemetry_incomplete():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, telemetry=False)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    blockers_text = " ".join(result.remaining_blockers)
    assert "telemetry_complete" in blockers_text


def test_ratify_blocked_when_live_evidence_checks_fail():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, all_checks=False)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False


def test_ratify_blocked_when_autonomy_violated():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, autonomy_preserved=False)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    blockers_text = " ".join(result.remaining_blockers)
    assert "local_autonomy_progress_preserved" in blockers_text


# ── live proof chain absent (no upgrade) ─────────────────────────────────────

def test_ratify_no_live_proof_notes_when_absent():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp)
    result = _make_ratifier(tmp).ratify()
    notes = result.final_summary.get("live_proof_notes", [])
    assert any("not found" in n for n in notes)


def test_ratify_live_proof_not_present_in_summary():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp)
    result = _make_ratifier(tmp).ratify()
    assert result.final_summary.get("live_proof_chain_present") is False


# ── live proof chain clears dispatch blocker ─────────────────────────────────

def test_ratify_clears_gate_with_live_proof():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    _write_live_proof_chain(tmp, dispatch_succeeded=True)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is True
    assert result.promotion_gate_cleared is True


def test_ratify_no_remaining_blockers_with_live_proof():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    _write_live_proof_chain(tmp, dispatch_succeeded=True)
    result = _make_ratifier(tmp).ratify()
    assert result.remaining_blockers == []


def test_ratify_live_evidence_seen_with_proof_chain():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp)
    _write_live_proof_chain(tmp, dispatch_succeeded=True)
    result = _make_ratifier(tmp).ratify()
    assert result.live_evidence_seen is True


def test_ratify_proof_chain_present_in_summary():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp)
    _write_live_proof_chain(tmp, dispatch_succeeded=True)
    result = _make_ratifier(tmp).ratify()
    assert result.final_summary.get("live_proof_chain_present") is True


def test_ratify_proof_notes_record_blocker_cleared():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    _write_live_proof_chain(tmp, dispatch_succeeded=True)
    result = _make_ratifier(tmp).ratify()
    notes = result.final_summary.get("live_proof_notes", [])
    assert any("cleared" in n for n in notes)


def test_ratify_proof_chain_failed_dispatch_does_not_clear():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    _write_live_proof_chain(tmp, dispatch_succeeded=False)
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is False
    assert len(result.remaining_blockers) >= 1


# ── full cleared state (all requirements met, live dispatch in live_evidence) ─

def test_ratify_clears_when_dispatch_succeeded_in_live_evidence():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=True, mode="live")
    result = _make_ratifier(tmp).ratify()
    assert result.phase7_final_ratified is True
    assert result.promotion_gate_cleared is True
    assert result.remaining_blockers == []


def test_ratify_summary_dispatch_mode_recorded():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    result = _make_ratifier(tmp).ratify()
    assert result.final_summary.get("dispatch_mode") == "dry_run_only"


def test_ratify_summary_total_blockers_accurate():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp, dispatch_succeeded=False, mode="dry_run_only")
    result = _make_ratifier(tmp).ratify()
    assert result.final_summary["total_blockers"] == len(result.remaining_blockers)


def test_ratify_summary_evidence_inputs_tracked():
    tmp = tempfile.mkdtemp()
    _write_promotion_pack(tmp)
    _write_live_evidence(tmp)
    result = _make_ratifier(tmp).ratify()
    ei = result.final_summary.get("evidence_inputs_loaded", {})
    assert "promotion_pack" in ei
    assert "live_evidence" in ei
    assert "live_proof_chain" in ei
    assert ei["promotion_pack"] is True
    assert ei["live_evidence"] is True
    assert ei["live_proof_chain"] is False


# ── real repo state: current state should be blocked on live dispatch ─────────

def test_ratify_real_repo_returns_result():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    result = r.ratify()
    assert result is not None


def test_ratify_real_repo_live_evidence_seen():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    result = r.ratify()
    assert result.live_evidence_seen is True


def test_ratify_real_repo_has_final_summary():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    result = r.ratify()
    assert isinstance(result.final_summary, dict)


def test_ratify_real_repo_truthful_not_ratified_without_live():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    result = r.ratify()
    # Aider not installed in current env; gate should be blocked on live dispatch
    # unless artifacts/local_runs/local_live_proof_chain.json exists with succeeded=True
    live_proof = REPO_ROOT / "artifacts" / "local_runs" / "local_live_proof_chain.json"
    if live_proof.exists():
        import json as _json
        chain = _json.loads(live_proof.read_text(encoding="utf-8"))
        if chain.get("live_dispatch_succeeded"):
            assert result.phase7_final_ratified is True
            return
    # No live proof chain present — expect gate blocked
    assert result.phase7_final_ratified is False


def test_ratify_real_repo_blocker_describes_live_dispatch():
    from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
    r = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    result = r.ratify()
    live_proof = REPO_ROOT / "artifacts" / "local_runs" / "local_live_proof_chain.json"
    if live_proof.exists():
        import json as _json
        chain = _json.loads(live_proof.read_text(encoding="utf-8"))
        if chain.get("live_dispatch_succeeded"):
            return  # gate cleared; no blocker expected
    blockers_text = " ".join(result.remaining_blockers)
    assert "live_dispatch" in blockers_text or "live" in blockers_text.lower()
