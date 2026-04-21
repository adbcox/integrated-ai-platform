"""Extended autonomy metrics for per-class breakdown and threshold gates.

Produces richer, machine-readable metrics from LocalMemoryStore:
first-pass success rate (approximate), per-task-class breakdown,
dominant error type, error type distribution, and threshold gates.

Note: first_pass_rate is an approximate success fraction derived from
stored success/failure counts. It does not track retries per session.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.local_memory_store import FailurePattern, LocalMemoryStore
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES

# -- import-time assertions --
assert callable(LocalMemoryStore.query_failures), "INTERFACE MISMATCH: LocalMemoryStore.query_failures"
assert callable(LocalMemoryStore.query_successes), "INTERFACE MISMATCH: LocalMemoryStore.query_successes"
assert callable(LocalMemoryStore.failure_rate), "INTERFACE MISMATCH: LocalMemoryStore.failure_rate"
assert "error_type" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.error_type"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "autonomy_metrics"
_DEFAULT_MIN_ATTEMPTS = 5
_DEFAULT_MAX_FAILURE_RATE = 0.30


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TaskClassMetricsExtended:
    task_class: str
    total_attempts: int
    successes: int
    failures: int
    failure_rate: float
    first_pass_rate: float
    dominant_error_type: str
    error_type_distribution: dict[str, int]


@dataclass
class ExtendedAutonomyMetrics:
    generated_at: str
    total_task_classes: int
    task_class_breakdown: list[TaskClassMetricsExtended] = field(default_factory=list)
    overall_successes: int = 0
    overall_failures: int = 0
    overall_failure_rate: float = 0.0
    overall_first_pass_rate: float = 0.0
    dominant_error_type: str = ""
    error_type_distribution: dict[str, int] = field(default_factory=dict)
    min_attempts_threshold: int = _DEFAULT_MIN_ATTEMPTS
    max_failure_rate_threshold: float = _DEFAULT_MAX_FAILURE_RATE

    def passes_thresholds(self) -> bool:
        """True if overall attempts >= min and failure_rate < max."""
        total = self.overall_successes + self.overall_failures
        return total >= self.min_attempts_threshold and self.overall_failure_rate < self.max_failure_rate_threshold

    def threshold_report(self) -> str:
        total = self.overall_successes + self.overall_failures
        lines = [
            f"attempts: {total} (threshold >= {self.min_attempts_threshold}) -> {'PASS' if total >= self.min_attempts_threshold else 'FAIL'}",
            f"failure_rate: {self.overall_failure_rate:.1%} (threshold < {self.max_failure_rate_threshold:.0%}) -> {'PASS' if self.overall_failure_rate < self.max_failure_rate_threshold else 'FAIL'}",
            f"passes_thresholds: {self.passes_thresholds()}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "generated_at": self.generated_at,
            "total_task_classes": self.total_task_classes,
            "overall_successes": self.overall_successes,
            "overall_failures": self.overall_failures,
            "overall_failure_rate": round(self.overall_failure_rate, 4),
            "overall_first_pass_rate": round(self.overall_first_pass_rate, 4),
            "dominant_error_type": self.dominant_error_type,
            "error_type_distribution": self.error_type_distribution,
            "passes_thresholds": self.passes_thresholds(),
            "task_class_breakdown": [
                {
                    "task_class": m.task_class,
                    "total_attempts": m.total_attempts,
                    "successes": m.successes,
                    "failures": m.failures,
                    "failure_rate": round(m.failure_rate, 4),
                    "first_pass_rate": round(m.first_pass_rate, 4),
                    "dominant_error_type": m.dominant_error_type,
                    "error_type_distribution": m.error_type_distribution,
                }
                for m in self.task_class_breakdown
            ],
        }


def _dominant_error(distribution: dict[str, int]) -> str:
    if not distribution:
        return ""
    return max(distribution, key=lambda k: distribution[k])


def collect_extended_metrics(
    *,
    memory_store: Optional[LocalMemoryStore] = None,
    min_attempts: int = _DEFAULT_MIN_ATTEMPTS,
    max_failure_rate: float = _DEFAULT_MAX_FAILURE_RATE,
) -> ExtendedAutonomyMetrics:
    """Collect per-class and overall extended autonomy metrics."""
    store = memory_store or LocalMemoryStore()

    breakdown: list[TaskClassMetricsExtended] = []
    overall_succ = 0
    overall_fail = 0
    global_error_dist: dict[str, int] = {}

    for tc in sorted(SUPPORTED_TASK_CLASSES):
        failures = store.query_failures(task_kind=tc, limit=10_000)
        successes = store.query_successes(task_kind=tc, limit=10_000)
        total = len(failures) + len(successes)
        rate = len(failures) / total if total > 0 else 0.0
        first_pass = len(successes) / total if total > 0 else 0.0

        err_dist: dict[str, int] = {}
        for f in failures:
            et = f.error_type or "unknown"
            err_dist[et] = err_dist.get(et, 0) + 1
            global_error_dist[et] = global_error_dist.get(et, 0) + 1

        breakdown.append(TaskClassMetricsExtended(
            task_class=tc,
            total_attempts=total,
            successes=len(successes),
            failures=len(failures),
            failure_rate=round(rate, 4),
            first_pass_rate=round(first_pass, 4),
            dominant_error_type=_dominant_error(err_dist),
            error_type_distribution=err_dist,
        ))
        overall_succ += len(successes)
        overall_fail += len(failures)

    overall_total = overall_succ + overall_fail
    overall_rate = overall_fail / overall_total if overall_total > 0 else 0.0
    overall_first_pass = overall_succ / overall_total if overall_total > 0 else 0.0

    return ExtendedAutonomyMetrics(
        generated_at=_iso_now(),
        total_task_classes=len(SUPPORTED_TASK_CLASSES),
        task_class_breakdown=breakdown,
        overall_successes=overall_succ,
        overall_failures=overall_fail,
        overall_failure_rate=round(overall_rate, 4),
        overall_first_pass_rate=round(overall_first_pass, 4),
        dominant_error_type=_dominant_error(global_error_dist),
        error_type_distribution=global_error_dist,
        min_attempts_threshold=min_attempts,
        max_failure_rate_threshold=max_failure_rate,
    )


def save_extended_metrics(
    metrics: ExtendedAutonomyMetrics,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[str]:
    """Write extended metrics to JSON artifact. Returns path or None on dry_run."""
    if dry_run:
        return None
    out_dir = Path(artifact_dir) if artifact_dir else _DEFAULT_ARTIFACT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = out_dir / "extended_metrics.json"
    artifact_file.write_text(
        json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(artifact_file)


__all__ = [
    "TaskClassMetricsExtended",
    "ExtendedAutonomyMetrics",
    "collect_extended_metrics",
    "save_extended_metrics",
]
