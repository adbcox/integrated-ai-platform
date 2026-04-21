"""LACE2-P9-REAL-FILE-RUNNER-SEAM-1: run real-file tasks via tmp fixture writes and readback verification."""
from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.real_file_benchmark_pack import RealFileTask, LACE2_REAL_FILE_PACK
from framework.real_file_benchmark_fixture import RealFileBenchmarkFixture, FixtureResult

assert "task_id" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.task_id"
assert "old_string" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.old_string"
assert "new_string" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.new_string"
assert "expected_content" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.expected_content"
assert "acceptance_grep" in RealFileTask.__dataclass_fields__, "INTERFACE MISMATCH: RealFileTask.acceptance_grep"


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
    actual_content: str
    failure_reason: Optional[str]


@dataclass
class Lace2BenchmarkRecord:
    run_id: str
    benchmark_kind: str
    total_tasks: int
    passed_count: int
    failed_count: int
    pass_rate: float
    kind_pass_rates: Dict[str, float]
    task_results: List[TaskRunResult]
    ran_at: str
    artifact_path: Optional[str] = None


def _apply_replacement(content: str, old_string: str, new_string: str) -> str:
    return content.replace(old_string, new_string, 1)


class Lace2BenchmarkRunner:
    """Runs LACE2 real-file benchmark via tmp fixture writes."""

    def __init__(self, tasks: tuple = LACE2_REAL_FILE_PACK):
        self._tasks = tasks
        self._fixture = RealFileBenchmarkFixture()

    def run(self) -> Lace2BenchmarkRecord:
        results: List[TaskRunResult] = []
        with tempfile.TemporaryDirectory(prefix="lace2_bench_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            for task in self._tasks:
                result = self._run_task(task, tmp_path)
                results.append(result)

        passed = sum(1 for r in results if r.passed)
        pass_rate = passed / len(results) if results else 0.0

        kind_buckets: Dict[str, list] = {}
        for r, t in zip(results, self._tasks):
            kind_buckets.setdefault(t.task_kind, []).append(r.passed)
        kind_pass_rates = {
            k: sum(v) / len(v) for k, v in kind_buckets.items()
        }

        return Lace2BenchmarkRecord(
            run_id=f"LACE2-RUN-{_ts()}",
            benchmark_kind="real_file_baseline",
            total_tasks=len(results),
            passed_count=passed,
            failed_count=len(results) - passed,
            pass_rate=round(pass_rate, 4),
            kind_pass_rates={k: round(v, 4) for k, v in kind_pass_rates.items()},
            task_results=results,
            ran_at=_iso_now(),
        )

    def _run_task(self, task: RealFileTask, tmp_dir: Path) -> TaskRunResult:
        fixture_result: FixtureResult = self._fixture.setup(task, tmp_dir)
        if not fixture_result.setup_ok:
            return TaskRunResult(
                task_id=task.task_id, task_kind=task.task_kind,
                passed=False, content_match=False, grep_match=False,
                actual_content="", failure_reason="fixture_setup_failed",
            )
        try:
            original = fixture_result.fixture_path.read_text(encoding="utf-8")
            updated = _apply_replacement(original, task.old_string, task.new_string)
            fixture_result.fixture_path.write_text(updated, encoding="utf-8")
            actual = fixture_result.fixture_path.read_text(encoding="utf-8")
        except OSError as exc:
            self._fixture.teardown(fixture_result)
            return TaskRunResult(
                task_id=task.task_id, task_kind=task.task_kind,
                passed=False, content_match=False, grep_match=False,
                actual_content="", failure_reason=f"io_error: {exc}",
            )

        content_match = actual == task.expected_content
        grep_match = bool(re.search(task.acceptance_grep, actual))
        passed = content_match and grep_match
        failure_reason = None
        if not passed:
            parts = []
            if not content_match:
                parts.append("content_mismatch")
            if not grep_match:
                parts.append("grep_failed")
            failure_reason = "|".join(parts)

        self._fixture.teardown(fixture_result)
        return TaskRunResult(
            task_id=task.task_id, task_kind=task.task_kind,
            passed=passed, content_match=content_match, grep_match=grep_match,
            actual_content=actual, failure_reason=failure_reason,
        )

    def emit(self, record: Lace2BenchmarkRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "lace2_benchmark_run.json"
        out_path.write_text(
            json.dumps({
                "run_id": record.run_id,
                "benchmark_kind": record.benchmark_kind,
                "total_tasks": record.total_tasks,
                "passed_count": record.passed_count,
                "failed_count": record.failed_count,
                "pass_rate": record.pass_rate,
                "kind_pass_rates": record.kind_pass_rates,
                "task_results": [asdict(r) for r in record.task_results],
                "ran_at": record.ran_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["TaskRunResult", "Lace2BenchmarkRecord", "Lace2BenchmarkRunner"]
