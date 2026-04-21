"""TaskClassBenchmarkRunner: per-task-class benchmark with inspection-first task-spec adaptation."""
from __future__ import annotations

import inspect as _inspect
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from framework.mvp_benchmark import MVPBenchmarkResult, MVPBenchmarkTaskSpec

# -- import-time inspection --
_bench_result_fields = set(MVPBenchmarkResult.__dataclass_fields__.keys())
assert "passed" in _bench_result_fields, \
    "INTERFACE MISMATCH: MVPBenchmarkResult.passed"
assert "failed" in _bench_result_fields, \
    "INTERFACE MISMATCH: MVPBenchmarkResult.failed"
assert "total_tasks" in _bench_result_fields, \
    "INTERFACE MISMATCH: MVPBenchmarkResult.total_tasks"

_spec_fields = set(MVPBenchmarkTaskSpec.__dataclass_fields__.keys())
assert "task_kind" in _spec_fields, "INTERFACE MISMATCH: MVPBenchmarkTaskSpec.task_kind"
assert "initial_content" in _spec_fields, "INTERFACE MISMATCH: MVPBenchmarkTaskSpec.initial_content"
assert "old_string" in _spec_fields, "INTERFACE MISMATCH: MVPBenchmarkTaskSpec.old_string"
assert "new_string" in _spec_fields, "INTERFACE MISMATCH: MVPBenchmarkTaskSpec.new_string"
assert "expected_content" in _spec_fields, "INTERFACE MISMATCH: MVPBenchmarkTaskSpec.expected_content"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _make_synthetic_spec(task_class: str, i: int) -> MVPBenchmarkTaskSpec:
    """Build a simple synthetic spec for a given task class."""
    if task_class == "text_replacement":
        old = f"VALUE_{i} = 0"
        new = f"VALUE_{i} = 1"
        content = f"# module\n{old}\n"
        expected = f"# module\n{new}\n"
    elif task_class == "metadata_addition":
        old = "# no metadata"
        new = "# metadata: added"
        content = f"{old}\nx = 1\n"
        expected = f"{new}\nx = 1\n"
    elif task_class == "helper_insertion":
        old = "def original():\n    pass"
        new = "def original():\n    pass\n\ndef helper():\n    return True"
        content = old + "\n"
        expected = new + "\n"
    else:
        old = f"# old_{i}"
        new = f"# new_{i}"
        content = f"{old}\n"
        expected = f"{new}\n"
    return MVPBenchmarkTaskSpec(
        task_id=f"synth-{task_class}-{i}",
        task_kind=task_class,
        file_name=f"synth_{task_class}_{i}.py",
        initial_content=content,
        old_string=old,
        new_string=new,
        expected_content=expected,
    )


def _run_spec_simple(spec: MVPBenchmarkTaskSpec) -> Dict[str, Any]:
    """Apply text replacement and compare to expected_content."""
    try:
        result_content = spec.initial_content.replace(spec.old_string, spec.new_string, 1)
        passed = result_content == spec.expected_content
    except Exception as exc:
        return {"task_id": spec.task_id, "task_kind": spec.task_kind, "passed": False, "error": str(exc)}
    return {
        "task_id": spec.task_id,
        "task_kind": spec.task_kind,
        "passed": passed,
        "error": None,
    }


@dataclass(frozen=True)
class TaskClassBenchmarkEntry:
    task_class: str
    total: int
    passed: int
    failed: int
    pass_rate: float


@dataclass(frozen=True)
class TaskClassBenchmarkReport:
    entries: Tuple[TaskClassBenchmarkEntry, ...]
    total_tasks: int
    total_passed: int
    total_failed: int
    overall_pass_rate: float
    evaluated_at: str
    artifact_path: Optional[str]


class TaskClassBenchmarkRunner:
    """Runs synthetic benchmark tasks per task class."""

    def __init__(self, *, artifact_root: Optional[Path] = None, tasks_per_class: int = 2):
        self._artifact_root = Path(artifact_root) if artifact_root is not None else Path("artifacts/task_class_benchmark")
        self._tasks_per_class = tasks_per_class

    def run(
        self,
        task_classes: Optional[List[str]] = None,
    ) -> TaskClassBenchmarkReport:
        if task_classes is None:
            task_classes = ["text_replacement", "metadata_addition", "helper_insertion"]

        entries = []
        total_tasks = 0
        total_passed = 0
        total_failed = 0

        for tc in task_classes:
            specs = [_make_synthetic_spec(tc, i) for i in range(self._tasks_per_class)]
            results = [_run_spec_simple(s) for s in specs]
            passed = sum(1 for r in results if r["passed"])
            failed = len(results) - passed
            entries.append(TaskClassBenchmarkEntry(
                task_class=tc,
                total=len(results),
                passed=passed,
                failed=failed,
                pass_rate=passed / len(results) if results else 0.0,
            ))
            total_tasks += len(results)
            total_passed += passed
            total_failed += failed

        overall_pass_rate = total_passed / total_tasks if total_tasks > 0 else 0.0
        artifact_path = self._emit_artifact(entries, total_tasks, total_passed, total_failed, overall_pass_rate)

        return TaskClassBenchmarkReport(
            entries=tuple(entries),
            total_tasks=total_tasks,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_pass_rate=overall_pass_rate,
            evaluated_at=_iso_now(),
            artifact_path=artifact_path,
        )

    def _emit_artifact(
        self,
        entries: List[TaskClassBenchmarkEntry],
        total_tasks: int,
        total_passed: int,
        total_failed: int,
        overall_pass_rate: float,
    ) -> str:
        self._artifact_root.mkdir(parents=True, exist_ok=True)
        out = self._artifact_root / "task_class_benchmark.json"
        out.write_text(
            json.dumps(
                {
                    "total_tasks": total_tasks,
                    "total_passed": total_passed,
                    "total_failed": total_failed,
                    "overall_pass_rate": overall_pass_rate,
                    "entries": [
                        {"task_class": e.task_class, "total": e.total, "passed": e.passed,
                         "failed": e.failed, "pass_rate": e.pass_rate}
                        for e in entries
                    ],
                    "evaluated_at": _iso_now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(out)


__all__ = ["TaskClassBenchmarkEntry", "TaskClassBenchmarkReport", "TaskClassBenchmarkRunner"]
