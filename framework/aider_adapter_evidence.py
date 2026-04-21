"""Aider adapter evidence gatherer for LAEC1.

Runs AiderRuntimeAdapter in dry-run mode across synthetic requests.
adapter_done is NEVER emitted from dry-run-only evidence.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.aider_adapter_contract import AiderAdapterConfig, AiderAdapterRequest, DEFAULT_AIDER_POLICY
from framework.aider_runtime_adapter import AiderRuntimeAdapter

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "aider_evidence"

AIDER_STATUS_DONE = "adapter_done"
AIDER_STATUS_PARTIAL = "adapter_partial"
AIDER_STATUS_DEFERRED = "adapter_deferred"

_SYNTHETIC_MODELS = [
    "ollama/qwen2.5-coder:14b",
    "ollama/deepseek-coder-v2:16b",
]
_SYNTHETIC_TASK_KINDS = ["text_replacement", "metadata_addition", "helper_insertion"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AiderAdapterEvidenceRecord:
    request_index: int
    model: str
    task_kind: str
    dry_run: bool
    success: bool
    exit_code: int
    stdout_snippet: str
    stderr_snippet: str

    def to_dict(self) -> dict:
        return {
            "request_index": self.request_index,
            "model": self.model,
            "task_kind": self.task_kind,
            "dry_run": self.dry_run,
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout_snippet": self.stdout_snippet[:120],
            "stderr_snippet": self.stderr_snippet[:120],
        }


@dataclass
class AiderAdapterEvidenceReport:
    overall_status: str
    records: list
    total_runs: int
    successful_runs: int
    failed_runs: int
    generated_at: str
    artifact_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "overall_status": self.overall_status,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "notes": self.notes,
            "generated_at": self.generated_at,
            "artifact_path": self.artifact_path,
            "records": [r.to_dict() for r in self.records],
        }


def gather_aider_evidence(
    *,
    num_runs: int = 3,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = True,
) -> AiderAdapterEvidenceReport:
    adapter = AiderRuntimeAdapter()
    records: list[AiderAdapterEvidenceRecord] = []

    for i in range(num_runs):
        model = _SYNTHETIC_MODELS[i % len(_SYNTHETIC_MODELS)]
        task_kind = _SYNTHETIC_TASK_KINDS[i % len(_SYNTHETIC_TASK_KINDS)]
        cfg = AiderAdapterConfig(
            model=model,
            target_files=[f"framework/synthetic_{task_kind}.py"],
            message=f"synthetic {task_kind} task {i}",
        )
        req = AiderAdapterRequest(config=cfg, session_id=f"evidence-{i}")
        artifact = adapter.run(req, dry_run=True)
        records.append(AiderAdapterEvidenceRecord(
            request_index=i,
            model=model,
            task_kind=task_kind,
            dry_run=True,
            success=artifact.success,
            exit_code=artifact.exit_code,
            stdout_snippet=artifact.stdout,
            stderr_snippet=artifact.stderr,
        ))

    successful = sum(1 for r in records if r.success)
    failed = len(records) - successful

    # Never emit adapter_done from dry-run-only evidence
    overall_status = AIDER_STATUS_PARTIAL if successful > 0 else AIDER_STATUS_DEFERRED
    notes = (
        "Dry-run-only evidence. adapter_done requires live binary evidence. "
        f"Ran {len(records)} synthetic requests in dry-run mode."
    )

    report = AiderAdapterEvidenceReport(
        overall_status=overall_status,
        records=records,
        total_runs=len(records),
        successful_runs=successful,
        failed_runs=failed,
        generated_at=_iso_now(),
        notes=notes,
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAEC1_aider_evidence.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "AIDER_STATUS_DONE",
    "AIDER_STATUS_PARTIAL",
    "AIDER_STATUS_DEFERRED",
    "AiderAdapterEvidenceRecord",
    "AiderAdapterEvidenceReport",
    "gather_aider_evidence",
]
