"""FirstPassMetric — distinguishes true first-attempt successes from retry-based successes.

Inspection gate output:
  LoopRetryStore.query_all sig: (self) -> list
  Returns list of dicts with: session_id, task_kind, attempt_number, success, error_type, recorded_at
  SUPPORTED_TASK_CLASSES: frozenset of known task classes
  first_pass success: attempt_number == 1 and success is True
  retry success: attempt_number > 1 and success is True
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.retry_telemetry_integration import LoopRetryStore
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES

assert callable(LoopRetryStore), "INTERFACE MISMATCH: LoopRetryStore not callable"
assert SUPPORTED_TASK_CLASSES, "INTERFACE MISMATCH: SUPPORTED_TASK_CLASSES empty"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "first_pass_metrics"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class FirstPassStat:
    task_kind: str
    total_attempts: int
    first_pass_successes: int
    retry_successes: int
    first_pass_rate: float
    retry_success_rate: float


@dataclass
class FirstPassReport:
    stats: list
    overall_first_pass_successes: int
    overall_retry_successes: int
    overall_attempts: int
    overall_first_pass_rate: float
    generated_at: str
    artifact_path: str = ""

    def summary_lines(self) -> list:
        lines = [f"FirstPassReport generated_at={self.generated_at}"]
        lines.append(f"  overall attempts={self.overall_attempts}")
        lines.append(f"  overall first_pass_rate={self.overall_first_pass_rate:.3f}")
        for s in self.stats:
            lines.append(
                f"  {s.task_kind}: attempts={s.total_attempts} "
                f"fp_rate={s.first_pass_rate:.3f} retry_rate={s.retry_success_rate:.3f}"
            )
        return lines

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "generated_at": self.generated_at,
            "overall_first_pass_successes": self.overall_first_pass_successes,
            "overall_retry_successes": self.overall_retry_successes,
            "overall_attempts": self.overall_attempts,
            "overall_first_pass_rate": round(self.overall_first_pass_rate, 4),
            "stats": [
                {
                    "task_kind": s.task_kind,
                    "total_attempts": s.total_attempts,
                    "first_pass_successes": s.first_pass_successes,
                    "retry_successes": s.retry_successes,
                    "first_pass_rate": round(s.first_pass_rate, 4),
                    "retry_success_rate": round(s.retry_success_rate, 4),
                }
                for s in self.stats
            ],
        }


def compute_first_pass_metrics(
    telemetry_store: LoopRetryStore,
    *,
    task_classes: Optional[frozenset] = None,
) -> FirstPassReport:
    all_records = telemetry_store.query_all()
    classes = task_classes if task_classes is not None else SUPPORTED_TASK_CLASSES

    # Group by task_kind
    by_kind: dict = {tc: [] for tc in classes}
    for rec in all_records:
        tk = rec.get("task_kind", "unknown")
        if tk in by_kind:
            by_kind[tk].append(rec)
        else:
            by_kind.setdefault(tk, []).append(rec)

    stats = []
    total_fp = 0
    total_retry = 0
    total_attempts = 0

    for task_kind, records in by_kind.items():
        n = len(records)
        fp_successes = sum(1 for r in records if r.get("attempt_number") == 1 and r.get("success") is True)
        retry_successes = sum(1 for r in records if r.get("attempt_number", 0) > 1 and r.get("success") is True)
        fp_rate = fp_successes / n if n > 0 else 0.0
        retry_rate = retry_successes / n if n > 0 else 0.0
        stats.append(FirstPassStat(
            task_kind=task_kind,
            total_attempts=n,
            first_pass_successes=fp_successes,
            retry_successes=retry_successes,
            first_pass_rate=fp_rate,
            retry_success_rate=retry_rate,
        ))
        total_fp += fp_successes
        total_retry += retry_successes
        total_attempts += n

    overall_fp_rate = total_fp / total_attempts if total_attempts > 0 else 0.0

    return FirstPassReport(
        stats=stats,
        overall_first_pass_successes=total_fp,
        overall_retry_successes=total_retry,
        overall_attempts=total_attempts,
        overall_first_pass_rate=overall_fp_rate,
        generated_at=_iso_now(),
    )


def save_first_pass_report(
    report: FirstPassReport,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> FirstPassReport:
    if dry_run:
        return report
    out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "first_pass_report.json"
    out_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    report.artifact_path = str(out_path)
    return report


__all__ = ["FirstPassStat", "FirstPassReport", "compute_first_pass_metrics", "save_first_pass_report"]
