"""LACE1-P11-FAILURE-PATTERN-MINING-SEAM-1: mine failure patterns from benchmark and rag4 usage."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.lace1_benchmark_runner import BenchmarkRunReport, TaskRunResult

assert "benchmark_kind" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.benchmark_kind"
assert "task_results" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.task_results"
assert "failure_reason" in TaskRunResult.__dataclass_fields__, "INTERFACE MISMATCH: TaskRunResult.failure_reason"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class FailurePattern:
    pattern_id: str
    pattern_kind: str
    description: str
    frequency: int
    severity: str          # "high" | "medium" | "low"
    source_ids: List[str]


@dataclass
class FailurePatternReport:
    report_id: str
    benchmark_failures: int
    retrieval_zero_boost_count: int
    total_patterns: int
    patterns: List[FailurePattern]
    mined_at: str
    artifact_path: Optional[str] = None


class FailurePatternMiner:
    """Mines failure patterns from benchmark results and stage_rag4 usage log."""

    def mine(
        self,
        report: BenchmarkRunReport,
        rag4_usage_path: Optional[Path] = None,
    ) -> FailurePatternReport:
        patterns: List[FailurePattern] = []

        # --- benchmark failure patterns ---
        bench_failures = [r for r in report.task_results if not r.passed]
        failure_reason_groups: dict = {}
        for r in bench_failures:
            reason = r.failure_reason or "unknown"
            failure_reason_groups.setdefault(reason, []).append(r.task_id)

        for reason, ids in failure_reason_groups.items():
            patterns.append(FailurePattern(
                pattern_id=f"BENCH-{reason.upper().replace(' ', '_')}",
                pattern_kind="benchmark_failure",
                description=f"Benchmark tasks failed with reason: {reason}",
                frequency=len(ids),
                severity="high" if len(ids) >= 3 else "medium",
                source_ids=ids,
            ))

        # --- retrieval patterns from rag4 usage ---
        zero_boost_ids: List[str] = []
        if rag4_usage_path is not None and Path(rag4_usage_path).exists():
            zero_boost_ids = _collect_zero_boost_queries(Path(rag4_usage_path))

        if zero_boost_ids:
            patterns.append(FailurePattern(
                pattern_id="RAG4-ZERO-ENTITY-BOOST",
                pattern_kind="retrieval_entity_boost_zero",
                description=(
                    "Queries where all retrieved targets had entity_boost=0.0 — "
                    "entity extraction did not improve ranking"
                ),
                frequency=len(zero_boost_ids),
                severity="medium" if len(zero_boost_ids) <= 5 else "high",
                source_ids=zero_boost_ids[:20],
            ))

        return FailurePatternReport(
            report_id=f"FPR-LACE1-{_ts()}",
            benchmark_failures=len(bench_failures),
            retrieval_zero_boost_count=len(zero_boost_ids),
            total_patterns=len(patterns),
            patterns=patterns,
            mined_at=_iso_now(),
        )

    def emit(self, report: FailurePatternReport, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "failure_patterns.json"
        payload = {
            "report_id": report.report_id,
            "benchmark_failures": report.benchmark_failures,
            "retrieval_zero_boost_count": report.retrieval_zero_boost_count,
            "total_patterns": report.total_patterns,
            "patterns": [asdict(p) for p in report.patterns],
            "mined_at": report.mined_at,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        report.artifact_path = str(out_path)
        return str(out_path)


def _collect_zero_boost_queries(path: Path) -> List[str]:
    """Return plan_ids where every target had entity_boost == 0.0."""
    zero_boost: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        targets = record.get("targets", [])
        if not targets:
            continue
        all_zero = all(
            t.get("selection_reason", {}).get("entity_boost", 0.0) == 0.0
            for t in targets
        )
        if all_zero:
            plan_id = record.get("plan_id") or record.get("query", "unknown")
            zero_boost.append(str(plan_id))
    return zero_boost


__all__ = ["FailurePattern", "FailurePatternReport", "FailurePatternMiner"]
