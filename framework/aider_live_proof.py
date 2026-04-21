"""AiderLiveProof — LAPC1 P3.

Attempts bounded Aider executions and emits AiderLiveProofReport.
Inspection gate confirmed:
  AiderRuntimeAdapter public methods: ['preflight', 'run']
  AiderAdapterArtifact fields: success, exit_code, stdout, stderr, dry_run, model,
                                target_files, session_id, artifact_path
  AiderLiveGateReport fields: checks, overall_result, live_execution_safe,
                               blocking_checks, generated_at, artifact_path
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.aider_runtime_adapter import AiderRuntimeAdapter as _AiderRuntimeAdapter
from framework.aider_adapter_contract import (
    AiderAdapterRequest as _AiderAdapterRequest,
    AiderAdapterConfig as _AiderAdapterConfig,
    AiderAdapterArtifact as _AiderAdapterArtifact,
    DEFAULT_AIDER_POLICY as _DEFAULT_AIDER_POLICY,
)
from framework.aider_live_execution_gate import AiderLiveGateReport as _AiderLiveGateReport, LIVE_GATE_PASS as _LIVE_GATE_PASS

assert hasattr(_AiderRuntimeAdapter, "run"), "INTERFACE MISMATCH: AiderRuntimeAdapter.run"
assert hasattr(_AiderRuntimeAdapter, "preflight"), "INTERFACE MISMATCH: AiderRuntimeAdapter.preflight"
assert "success" in _AiderAdapterArtifact.__dataclass_fields__, "INTERFACE MISMATCH: AiderAdapterArtifact.success"
assert "exit_code" in _AiderAdapterArtifact.__dataclass_fields__, "INTERFACE MISMATCH: AiderAdapterArtifact.exit_code"
assert "config" in _AiderAdapterRequest.__dataclass_fields__, "INTERFACE MISMATCH: AiderAdapterRequest.config"
assert "model" in _AiderAdapterConfig.__dataclass_fields__, "INTERFACE MISMATCH: AiderAdapterConfig.model"
assert "message" in _AiderAdapterConfig.__dataclass_fields__, "INTERFACE MISMATCH: AiderAdapterConfig.message"
assert "target_files" in _AiderAdapterConfig.__dataclass_fields__, "INTERFACE MISMATCH: AiderAdapterConfig.target_files"
assert "live_execution_safe" in _AiderLiveGateReport.__dataclass_fields__, "INTERFACE MISMATCH: AiderLiveGateReport.live_execution_safe"
assert "overall_result" in _AiderLiveGateReport.__dataclass_fields__, "INTERFACE MISMATCH: AiderLiveGateReport.overall_result"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "aider_live_proof"
_SYNTHETIC_MODELS = ["ollama/qwen2.5-coder:14b", "ollama/deepseek-coder-v2:16b"]
_SYNTHETIC_TASK_KINDS = ["text_replacement", "helper_insertion", "metadata_addition"]

PROOF_STATUS_LIVE_PROVEN = "live_proven"
PROOF_STATUS_DRY_RUN_ONLY = "dry_run_only"
PROOF_STATUS_BLOCKED = "blocked"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AiderLiveProofRecord:
    run_index: int
    model: str
    task_kind: str
    attempted_live: bool
    dry_run_used: bool
    success: bool
    exit_code: int
    proof_detail: str

    def to_dict(self) -> dict:
        return {
            "run_index": self.run_index,
            "model": self.model,
            "task_kind": self.task_kind,
            "attempted_live": self.attempted_live,
            "dry_run_used": self.dry_run_used,
            "success": self.success,
            "exit_code": self.exit_code,
            "proof_detail": self.proof_detail,
        }


@dataclass
class AiderLiveProofReport:
    proof_status: str
    records: list
    total_runs: int
    successful_runs: int
    gate_result: str
    live_execution_safe: bool
    notes: str
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "proof_status": self.proof_status,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "gate_result": self.gate_result,
            "live_execution_safe": self.live_execution_safe,
            "notes": self.notes,
            "generated_at": self.generated_at,
            "records": [r.to_dict() for r in self.records],
        }


def run_aider_live_proof(
    gate_report: _AiderLiveGateReport,
    *,
    num_runs: int = 3,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> AiderLiveProofReport:
    adapter = _AiderRuntimeAdapter()
    records = []

    for i in range(num_runs):
        model = _SYNTHETIC_MODELS[i % len(_SYNTHETIC_MODELS)]
        task_kind = _SYNTHETIC_TASK_KINDS[i % len(_SYNTHETIC_TASK_KINDS)]
        config = _AiderAdapterConfig(
            model=model,
            target_files=[],
            message=f"dry-run proof run {i}: {task_kind}",
            policy=_DEFAULT_AIDER_POLICY,
        )
        request = _AiderAdapterRequest(config=config)

        if gate_report.live_execution_safe:
            # Attempt live execution
            result = adapter.run(request, dry_run=False)
            attempted_live = True
            dry_run_used = False
        else:
            # Gate blocked — fall back to dry-run only
            result = adapter.run(request, dry_run=True)
            attempted_live = False
            dry_run_used = True

        records.append(AiderLiveProofRecord(
            run_index=i,
            model=model,
            task_kind=task_kind,
            attempted_live=attempted_live,
            dry_run_used=dry_run_used,
            success=result.success,
            exit_code=result.exit_code,
            proof_detail=f"stdout={result.stdout[:80]!r}" if result.stdout else "no stdout",
        ))

    successful_runs = sum(1 for r in records if r.success)

    if gate_report.live_execution_safe and successful_runs >= 1:
        proof_status = PROOF_STATUS_LIVE_PROVEN
        notes = f"Live execution gate passed; {successful_runs}/{num_runs} live runs succeeded."
    else:
        proof_status = PROOF_STATUS_BLOCKED
        notes = (
            f"Live execution gate blocked ({gate_report.blocking_checks}). "
            "Fell back to dry-run proof only. "
            "Gate unblocked when 'aider' registered in KNOWN_FRAMEWORK_COMMANDS "
            "and preflight reports pass."
        )

    report = AiderLiveProofReport(
        proof_status=proof_status,
        records=records,
        total_runs=num_runs,
        successful_runs=successful_runs,
        gate_result=gate_report.overall_result,
        live_execution_safe=gate_report.live_execution_safe,
        notes=notes,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_aider_live_proof.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "PROOF_STATUS_LIVE_PROVEN",
    "PROOF_STATUS_DRY_RUN_ONLY",
    "PROOF_STATUS_BLOCKED",
    "AiderLiveProofRecord",
    "AiderLiveProofReport",
    "run_aider_live_proof",
]
