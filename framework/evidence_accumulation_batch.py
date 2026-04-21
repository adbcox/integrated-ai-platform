"""EvidenceAccumulationBatch — runs TaskRepetitionHarness across all safe task kinds.

Inspection gate output:
  SAFE_TASK_KINDS: frozenset({'metadata_addition', 'helper_insertion', 'text_replacement'})
  make_synthetic_repetition_tasks sig: (task_kind: str, num_tasks: int, tmp_dir: Path) -> list[dict]
  TaskRepetitionHarness.run sig: (self, config: RepetitionRunConfig, tasks: list[dict]) -> RepetitionRunResult
  RepetitionRunConfig fields: task_kind, num_runs, dry_run, artifact_dir
  RepetitionRunResult fields: config, records, total_runs, success_count, failure_count, started_at, finished_at
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.mvp_coding_loop import SAFE_TASK_KINDS
from framework.task_repetition_harness import (
    RepetitionRunConfig,
    RepetitionRunResult,
    TaskRepetitionHarness,
    make_synthetic_repetition_tasks,
)

assert SAFE_TASK_KINDS, "INTERFACE MISMATCH: SAFE_TASK_KINDS empty"
assert callable(TaskRepetitionHarness), "INTERFACE MISMATCH: TaskRepetitionHarness not callable"
assert callable(make_synthetic_repetition_tasks), "INTERFACE MISMATCH: make_synthetic_repetition_tasks not callable"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "evidence_accumulation"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class BatchRunConfig:
    runs_per_kind: int = 3
    dry_run: bool = True
    artifact_dir: Optional[Path] = None


@dataclass
class BatchKindResult:
    task_kind: str
    total_runs: int
    success_count: int
    failure_count: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_kind": self.task_kind,
            "total_runs": self.total_runs,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error": self.error,
        }


@dataclass
class BatchRunResult:
    config: BatchRunConfig
    kind_results: list
    total_kinds: int
    total_runs: int
    total_successes: int
    total_failures: int
    generated_at: str
    artifact_path: str = ""

    def summary_line(self) -> str:
        return (
            f"BatchRunResult kinds={self.total_kinds} runs={self.total_runs} "
            f"successes={self.total_successes} failures={self.total_failures}"
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "generated_at": self.generated_at,
            "total_kinds": self.total_kinds,
            "total_runs": self.total_runs,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "kind_results": [kr.to_dict() for kr in self.kind_results],
        }


class EvidenceAccumulationBatch:
    """Runs TaskRepetitionHarness across all safe task kinds in batch mode."""

    def __init__(self, harness: Optional[TaskRepetitionHarness] = None) -> None:
        self._harness = harness if harness is not None else TaskRepetitionHarness()

    def run(self, config: BatchRunConfig) -> BatchRunResult:
        kind_results = []
        total_runs = 0
        total_successes = 0
        total_failures = 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            for task_kind in sorted(SAFE_TASK_KINDS):
                try:
                    tasks = make_synthetic_repetition_tasks(task_kind, config.runs_per_kind, Path(tmp_dir))
                    run_config = RepetitionRunConfig(
                        task_kind=task_kind,
                        num_runs=config.runs_per_kind,
                        dry_run=config.dry_run,
                        artifact_dir=config.artifact_dir,
                    )
                    result = self._harness.run(run_config, tasks)
                    kr = BatchKindResult(
                        task_kind=task_kind,
                        total_runs=result.total_runs,
                        success_count=result.success_count,
                        failure_count=result.failure_count,
                    )
                    total_runs += result.total_runs
                    total_successes += result.success_count
                    total_failures += result.failure_count
                except Exception as exc:  # noqa: BLE001
                    kr = BatchKindResult(
                        task_kind=task_kind,
                        total_runs=0,
                        success_count=0,
                        failure_count=0,
                        error=str(exc),
                    )
                kind_results.append(kr)

        batch_result = BatchRunResult(
            config=config,
            kind_results=kind_results,
            total_kinds=len(kind_results),
            total_runs=total_runs,
            total_successes=total_successes,
            total_failures=total_failures,
            generated_at=_iso_now(),
        )

        if not config.dry_run:
            out_dir = Path(config.artifact_dir) if config.artifact_dir else _DEFAULT_ARTIFACT_DIR
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "batch_run_result.json"
            out_path.write_text(json.dumps(batch_result.to_dict(), indent=2), encoding="utf-8")
            batch_result.artifact_path = str(out_path)

        return batch_result


__all__ = ["BatchRunConfig", "BatchKindResult", "BatchRunResult", "EvidenceAccumulationBatch"]
