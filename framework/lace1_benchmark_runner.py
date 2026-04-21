"""LACE1-P10-BENCHMARK-RUNNER-SEAM-1: deterministic benchmark runner for LACE1 task pack."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.local_autonomy_benchmark_pack import LocalAutonomyTask, LACE1_TASK_PACK

assert "task_id" in LocalAutonomyTask.__dataclass_fields__, "INTERFACE MISMATCH: LocalAutonomyTask.task_id"
assert "acceptance_grep" in LocalAutonomyTask.__dataclass_fields__, "INTERFACE MISMATCH: LocalAutonomyTask.acceptance_grep"
assert "expected_content" in LocalAutonomyTask.__dataclass_fields__, "INTERFACE MISMATCH: LocalAutonomyTask.expected_content"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class TaskRunResult:
    task_id: str
    task_kind: str
    passed: bool
    content_match: bool
    grep_match: bool
    failure_reason: Optional[str]


@dataclass
class BenchmarkRunReport:
    run_id: str
    benchmark_kind: str
    total_tasks: int
    passed: int
    failed: int
    pass_rate: float
    task_results: List[TaskRunResult]
    run_at: str
    artifact_path: Optional[str] = None


class Lace1BenchmarkRunner:
    """Runs LACE1 task pack deterministically via string replacement — no LLM involved."""

    def run(self, tasks: tuple = LACE1_TASK_PACK) -> BenchmarkRunReport:
        results: List[TaskRunResult] = []

        for task in tasks:
            result = self._run_task(task)
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        total = len(results)
        pass_rate = passed / total if total > 0 else 0.0

        return BenchmarkRunReport(
            run_id=f"LACE1-BENCH-{_ts()}",
            benchmark_kind="synthetic_baseline",
            total_tasks=total,
            passed=passed,
            failed=total - passed,
            pass_rate=pass_rate,
            task_results=results,
            run_at=_iso_now(),
        )

    def _run_task(self, task: LocalAutonomyTask) -> TaskRunResult:
        actual_content = task.initial_content.replace(task.old_string, task.new_string, 1)
        content_match = actual_content == task.expected_content

        try:
            grep_match = bool(re.search(task.acceptance_grep, actual_content))
        except re.error as exc:
            return TaskRunResult(
                task_id=task.task_id,
                task_kind=task.task_kind,
                passed=False,
                content_match=content_match,
                grep_match=False,
                failure_reason=f"invalid acceptance_grep: {exc}",
            )

        passed = content_match and grep_match
        failure_reason: Optional[str] = None
        if not content_match:
            failure_reason = "content_mismatch"
        elif not grep_match:
            failure_reason = "grep_not_found"

        return TaskRunResult(
            task_id=task.task_id,
            task_kind=task.task_kind,
            passed=passed,
            content_match=content_match,
            grep_match=grep_match,
            failure_reason=failure_reason,
        )

    def emit(self, report: BenchmarkRunReport, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{report.run_id}.json"
        payload = {
            "run_id": report.run_id,
            "benchmark_kind": report.benchmark_kind,
            "total_tasks": report.total_tasks,
            "passed": report.passed,
            "failed": report.failed,
            "pass_rate": report.pass_rate,
            "run_at": report.run_at,
            "task_results": [asdict(r) for r in report.task_results],
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        report.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["TaskRunResult", "BenchmarkRunReport", "Lace1BenchmarkRunner"]
