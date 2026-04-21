"""EvidenceBackedTaskExpander: evaluates whether additional task classes should be added to safe family."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from framework.task_class_benchmark import TaskClassBenchmarkReport
from framework.unified_local_metrics import UnifiedLocalMetrics

# -- import-time assertions --
assert "overall_pass_rate" in TaskClassBenchmarkReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassBenchmarkReport.overall_pass_rate"
assert "total_tasks" in TaskClassBenchmarkReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassBenchmarkReport.total_tasks"
assert "first_pass_rate" in UnifiedLocalMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: UnifiedLocalMetrics.first_pass_rate"
assert "failure_rate" in UnifiedLocalMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: UnifiedLocalMetrics.failure_rate"

EXPANSION_CANDIDATES = ("bug_fix", "narrow_test_update")

_MIN_BENCHMARK_TASKS = 4
_MIN_PASS_RATE = 0.80
_MAX_FAILURE_RATE = 0.20
_MIN_FIRST_PASS_RATE = 0.70


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class TaskExpansionDecision:
    task_class: str
    decision: str  # "expand" | "insufficient_evidence" | "not_ready"
    rationale: str


@dataclass(frozen=True)
class TaskExpansionRecord:
    decisions: Tuple[TaskExpansionDecision, ...]
    expansion_candidates: Tuple[str, ...]
    evaluated_at: str
    artifact_path: Optional[str]


class EvidenceBackedTaskExpander:
    """Evaluates task class expansion; conservative by default — insufficient_evidence for non-benchmarked classes."""

    def evaluate(
        self,
        *,
        benchmark_report: Optional[TaskClassBenchmarkReport] = None,
        unified_metrics: Optional[UnifiedLocalMetrics] = None,
        candidates: Optional[List[str]] = None,
    ) -> TaskExpansionRecord:
        if candidates is None:
            candidates = list(EXPANSION_CANDIDATES)

        decisions = []
        for tc in candidates:
            decision = self._decide(tc, benchmark_report=benchmark_report, metrics=unified_metrics)
            decisions.append(decision)

        return TaskExpansionRecord(
            decisions=tuple(decisions),
            expansion_candidates=tuple(candidates),
            evaluated_at=_iso_now(),
            artifact_path=None,
        )

    def _decide(
        self,
        task_class: str,
        *,
        benchmark_report: Optional[TaskClassBenchmarkReport],
        metrics: Optional[UnifiedLocalMetrics],
    ) -> TaskExpansionDecision:
        if benchmark_report is None or metrics is None:
            return TaskExpansionDecision(
                task_class=task_class,
                decision="insufficient_evidence",
                rationale="No benchmark report or unified metrics available",
            )

        # Check if this task class was directly benchmarked
        benchmarked_classes = {e.task_class for e in benchmark_report.entries}
        if task_class not in benchmarked_classes:
            return TaskExpansionDecision(
                task_class=task_class,
                decision="insufficient_evidence",
                rationale=f"Task class '{task_class}' was not directly benchmarked in this campaign",
            )

        # Find entry for this class
        entry = next(e for e in benchmark_report.entries if e.task_class == task_class)
        if entry.total < _MIN_BENCHMARK_TASKS:
            return TaskExpansionDecision(
                task_class=task_class,
                decision="insufficient_evidence",
                rationale=f"Only {entry.total} benchmark tasks (minimum {_MIN_BENCHMARK_TASKS} required)",
            )

        if entry.pass_rate < _MIN_PASS_RATE:
            return TaskExpansionDecision(
                task_class=task_class,
                decision="not_ready",
                rationale=f"Pass rate {entry.pass_rate:.0%} below minimum {_MIN_PASS_RATE:.0%}",
            )

        if metrics.failure_rate > _MAX_FAILURE_RATE:
            return TaskExpansionDecision(
                task_class=task_class,
                decision="not_ready",
                rationale=f"System failure rate {metrics.failure_rate:.0%} too high for expansion",
            )

        if metrics.first_pass_rate < _MIN_FIRST_PASS_RATE:
            return TaskExpansionDecision(
                task_class=task_class,
                decision="insufficient_evidence",
                rationale=f"First-pass rate {metrics.first_pass_rate:.0%} below threshold {_MIN_FIRST_PASS_RATE:.0%}",
            )

        return TaskExpansionDecision(
            task_class=task_class,
            decision="expand",
            rationale=f"Pass rate {entry.pass_rate:.0%}, failure rate {metrics.failure_rate:.0%}, first-pass {metrics.first_pass_rate:.0%}",
        )


def emit_expansion_record(
    record: TaskExpansionRecord,
    *,
    artifact_dir: Path = Path("artifacts") / "task_expansion",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "task_expansion_record.json"
    out_path.write_text(
        json.dumps(
            {
                "expansion_candidates": list(record.expansion_candidates),
                "evaluated_at": record.evaluated_at,
                "decisions": [
                    {"task_class": d.task_class, "decision": d.decision, "rationale": d.rationale}
                    for d in record.decisions
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = [
    "EXPANSION_CANDIDATES",
    "TaskExpansionDecision",
    "TaskExpansionRecord",
    "EvidenceBackedTaskExpander",
    "emit_expansion_record",
]
