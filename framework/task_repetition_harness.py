"""Task repetition harness for safe real-run evidence accumulation.

Runs the local MVP loop multiple times against the safe task family, records all
outcomes into LocalMemoryStore, and produces a RepetitionRunResult artifact.

Inspection gate output (packet 5):
  MVPCodingLoopRunner.__init__ sig: (self, session_like, workspace_like, gate, scope, *, runner=None, source_root=None)
  MVPCodingLoopRunner.run_task sig: (self, task: MVPTask) -> MVPLoopResult
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.mvp_coding_loop import MVPCodingLoopRunner, MVPLoopResult, MVPTask
from framework.local_memory_store import LocalMemoryStore

# -- import-time assertions --
assert hasattr(MVPCodingLoopRunner, "run_task"), "INTERFACE MISMATCH: MVPCodingLoopRunner.run_task"
assert hasattr(MVPTask, "__dataclass_fields__"), "INTERFACE MISMATCH: MVPTask is not a dataclass"
assert hasattr(MVPLoopResult, "__dataclass_fields__"), "INTERFACE MISMATCH: MVPLoopResult is not a dataclass"
assert callable(LocalMemoryStore.record_success), "INTERFACE MISMATCH: LocalMemoryStore.record_success"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class RepetitionRunConfig:
    task_kind: str
    num_runs: int
    dry_run: bool = False
    artifact_dir: Optional[str] = None


@dataclass
class RepetitionRunRecord:
    task_kind: str
    run_index: int
    success: bool
    error_message: str
    duration_seconds: float
    recorded_at: str


@dataclass
class RepetitionRunResult:
    config: RepetitionRunConfig
    records: list[RepetitionRunRecord] = field(default_factory=list)
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0
    started_at: str = field(default_factory=_iso_now)
    finished_at: str = field(default_factory=_iso_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "task_kind": self.config.task_kind,
            "num_runs": self.config.num_runs,
            "dry_run": self.config.dry_run,
            "total_runs": self.total_runs,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "records": [asdict(r) for r in self.records],
        }

    def summary_line(self) -> str:
        rate = self.success_count / self.total_runs if self.total_runs > 0 else 0.0
        return (
            f"{self.config.task_kind}: {self.total_runs} runs, "
            f"{self.success_count} success, {self.failure_count} failure "
            f"({rate:.1%} pass rate)"
        )


class TaskRepetitionHarness:
    """Runs synthetic tasks through the MVP loop and records outcomes."""

    def __init__(
        self,
        memory_store: Optional[LocalMemoryStore] = None,
        loop_runner: Optional[Any] = None,
    ) -> None:
        self._store = memory_store or LocalMemoryStore()
        self._runner = loop_runner

    def run(
        self,
        config: RepetitionRunConfig,
        tasks: list[dict],
    ) -> RepetitionRunResult:
        """Iterate tasks, run or simulate, record outcomes, return result."""
        started_at = _iso_now()
        records: list[RepetitionRunRecord] = []

        for i, task_dict in enumerate(tasks[: config.num_runs]):
            t_start = time.perf_counter()

            if config.dry_run:
                success = True
                error_msg = ""
            elif self._runner is not None:
                try:
                    mvp_task = MVPTask(
                        session_id=task_dict.get("session_id", f"rep-{i}"),
                        target_path=task_dict["target_path"],
                        old_string=task_dict["old_string"],
                        new_string=task_dict["new_string"],
                        task_kind=task_dict.get("task_kind", config.task_kind),
                    )
                    loop_result: MVPLoopResult = self._runner.run_task(mvp_task)
                    success = loop_result.success
                    error_msg = getattr(loop_result, "error_message", "") or ""
                except Exception as exc:
                    success = False
                    error_msg = str(exc)
            else:
                success = False
                error_msg = "no loop_runner provided and dry_run=False"

            duration = time.perf_counter() - t_start

            if not config.dry_run:
                if success:
                    self._store.record_success(
                        task_kind=config.task_kind,
                        target_file=task_dict.get("target_path", ""),
                        old_string=task_dict.get("old_string", ""),
                        new_string=task_dict.get("new_string", ""),
                    )
                else:
                    self._store.record_failure(
                        task_kind=config.task_kind,
                        target_file=task_dict.get("target_path", ""),
                        old_string=task_dict.get("old_string", ""),
                        error=error_msg,
                    )

            records.append(RepetitionRunRecord(
                task_kind=config.task_kind,
                run_index=i,
                success=success,
                error_message=error_msg,
                duration_seconds=round(duration, 4),
                recorded_at=_iso_now(),
            ))

        success_count = sum(1 for r in records if r.success)
        return RepetitionRunResult(
            config=config,
            records=records,
            total_runs=len(records),
            success_count=success_count,
            failure_count=len(records) - success_count,
            started_at=started_at,
            finished_at=_iso_now(),
        )


def make_synthetic_repetition_tasks(
    task_kind: str,
    num_tasks: int,
    tmp_dir: Path,
) -> list[dict]:
    """Create real temp-backed synthetic tasks for repetition testing."""
    tasks = []
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for i in range(num_tasks):
        target = tmp_dir / f"task_{i}.py"
        old_s = f"placeholder_{i} = 'old'"
        new_s = f"placeholder_{i} = 'new'"
        target.write_text(f"{old_s}\n", encoding="utf-8")
        tasks.append({
            "session_id": f"synth-{i}",
            "target_path": str(target),
            "old_string": old_s,
            "new_string": new_s,
            "task_kind": task_kind,
        })
    return tasks


__all__ = [
    "RepetitionRunConfig",
    "RepetitionRunRecord",
    "RepetitionRunResult",
    "TaskRepetitionHarness",
    "make_synthetic_repetition_tasks",
]
