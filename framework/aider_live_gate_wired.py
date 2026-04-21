"""APCC1-P4: Wired Aider gate and proof using fully wired preflight checker."""
from __future__ import annotations

import inspect as _inspect
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --- Inspection gate ---
from framework.aider_runtime_adapter import AiderRuntimeAdapter as _ARA
from framework.aider_live_execution_gate import (
    AiderLiveGateReport,
    AiderLiveGateCheck,
    LIVE_GATE_PASS,
    LIVE_GATE_BLOCK,
)
from framework.aider_live_proof import (
    AiderLiveProofReport,
    AiderLiveProofRecord,
    PROOF_STATUS_BLOCKED,
    PROOF_STATUS_LIVE_PROVEN,
    PROOF_STATUS_DRY_RUN_ONLY,
)

_ARA_SIG = str(_inspect.signature(_ARA.__init__))
_ARA_ACCEPTS_CHECKER = "preflight_checker" in _ARA_SIG


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_wired_aider_gate(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> AiderLiveGateReport:
    from framework.aider_config_provider import make_fully_wired_preflight_checker

    checker = make_fully_wired_preflight_checker()
    preflight_result = checker.run_preflight()

    blocking_names = {"aider_importable", "permission_gate_active", "config_keys_present"}

    gate_checks = []
    blocking_check_names = []
    for pc in preflight_result.checks:
        gate_check = AiderLiveGateCheck(
            check_name=pc.check_name,
            passed=pc.passed,
            observed_value="True" if pc.passed else "False",
            required_value="True",
            detail=pc.detail,
        )
        gate_checks.append(gate_check)
        if pc.check_name in blocking_names and not pc.passed:
            blocking_check_names.append(pc.check_name)

    live_safe = len(blocking_check_names) == 0
    overall = LIVE_GATE_PASS if live_safe else LIVE_GATE_BLOCK

    report = AiderLiveGateReport(
        checks=tuple(gate_checks),
        overall_result=overall,
        live_execution_safe=live_safe,
        blocking_checks=tuple(blocking_check_names),
        generated_at=_iso_now(),
        artifact_path=None,
    )
    return report


def run_wired_aider_proof(
    gate_report: AiderLiveGateReport,
    *,
    num_runs: int = 3,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> AiderLiveProofReport:
    if not gate_report.live_execution_safe:
        records = [
            AiderLiveProofRecord(
                run_index=i,
                model="n/a",
                task_kind="bounded_proof",
                attempted_live=False,
                dry_run_used=True,
                success=False,
                exit_code=-1,
                proof_detail="gate blocked — live execution not safe",
            )
            for i in range(num_runs)
        ]
        return AiderLiveProofReport(
            proof_status=PROOF_STATUS_BLOCKED,
            records=tuple(records),
            total_runs=num_runs,
            successful_runs=0,
            gate_result=gate_report.overall_result,
            live_execution_safe=False,
            notes="Gate blocked; wired checker not sufficient to unblock this path.",
            generated_at=_iso_now(),
            artifact_path=None,
        )

    # Gate passed — live_execution_safe is True
    notes_parts = []
    if not _ARA_ACCEPTS_CHECKER:
        notes_parts.append(
            "RESIDUAL GAP: AiderRuntimeAdapter constructor does not accept preflight_checker kwarg "
            f"(sig={_ARA_SIG}). Wired checker cannot be injected into adapter. "
            "Adapter will run its own unpatched preflight internally."
        )

    if dry_run:
        records = [
            AiderLiveProofRecord(
                run_index=i,
                model="dry_run",
                task_kind="bounded_proof",
                attempted_live=False,
                dry_run_used=True,
                success=True,
                exit_code=0,
                proof_detail="dry_run=True; gate safe; proof deferred",
            )
            for i in range(num_runs)
        ]
        return AiderLiveProofReport(
            proof_status=PROOF_STATUS_DRY_RUN_ONLY,
            records=tuple(records),
            total_runs=num_runs,
            successful_runs=0,
            gate_result=gate_report.overall_result,
            live_execution_safe=True,
            notes="; ".join(notes_parts) if notes_parts else "dry_run mode",
            generated_at=_iso_now(),
            artifact_path=None,
        )

    # Live attempt — adapter runs its own preflight; if it fails, records will show failure
    from framework.aider_runtime_adapter import AiderRuntimeAdapter
    from framework.aider_adapter_contract import AiderAdapterRequest, DEFAULT_AIDER_POLICY, AiderAdapterConfig

    adapter = AiderRuntimeAdapter()
    records = []
    successful = 0

    for i in range(num_runs):
        req = AiderAdapterRequest(
            config=AiderAdapterConfig(
                model="gpt-4o",
                target_files=[],
                message="echo bounded_proof_run",
                policy=DEFAULT_AIDER_POLICY,
                dry_run=False,
            ),
            session_id=f"apcc1_p4_{i}",
        )
        try:
            artifact = adapter.run(req)
            ok = artifact.status == "done"
        except Exception as exc:
            ok = False
            artifact = None

        detail = (
            artifact.notes if artifact and hasattr(artifact, "notes") and artifact.notes
            else ("success" if ok else "adapter failed")
        )
        records.append(AiderLiveProofRecord(
            run_index=i,
            model="gpt-4o",
            task_kind="bounded_proof",
            attempted_live=True,
            dry_run_used=False,
            success=ok,
            exit_code=0 if ok else 1,
            proof_detail=str(detail)[:200],
        ))
        if ok:
            successful += 1

    proof_status = PROOF_STATUS_LIVE_PROVEN if successful >= 1 else PROOF_STATUS_BLOCKED
    notes = "; ".join(notes_parts) if notes_parts else "wired live proof run"

    return AiderLiveProofReport(
        proof_status=proof_status,
        records=tuple(records),
        total_runs=num_runs,
        successful_runs=successful,
        gate_result=gate_report.overall_result,
        live_execution_safe=True,
        notes=notes,
        generated_at=_iso_now(),
        artifact_path=None,
    )
