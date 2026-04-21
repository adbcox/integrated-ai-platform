"""LACE2-P10-REGIME-COMPARATOR-SEAM-1: compare LACE1 synthetic vs LACE2 real-file benchmark regimes."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from framework.lace1_benchmark_runner import Lace1BenchmarkRunner, BenchmarkRunReport
from framework.lace2_benchmark_runner import Lace2BenchmarkRunner, Lace2BenchmarkRecord

assert "benchmark_kind" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.benchmark_kind"
assert "pass_rate" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.pass_rate"
assert "total_tasks" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.total_tasks"
assert "benchmark_kind" in Lace2BenchmarkRecord.__dataclass_fields__, "INTERFACE MISMATCH: Lace2BenchmarkRecord.benchmark_kind"
assert "pass_rate" in Lace2BenchmarkRecord.__dataclass_fields__, "INTERFACE MISMATCH: Lace2BenchmarkRecord.pass_rate"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class RegimeComparisonRecord:
    comparison_id: str
    lace1_benchmark_kind: str
    lace1_total_tasks: int
    lace1_pass_rate: float
    lace2_benchmark_kind: str
    lace2_total_tasks: int
    lace2_pass_rate: float
    pass_rate_delta: float
    regime_upgrade_confirmed: bool
    compared_at: str
    artifact_path: Optional[str] = None


class BenchmarkRegimeComparator:
    """Runs both benchmark regimes and compares synthetic vs real-file pass rates."""

    def compare(self) -> RegimeComparisonRecord:
        lace1_report: BenchmarkRunReport = Lace1BenchmarkRunner().run()
        lace2_record: Lace2BenchmarkRecord = Lace2BenchmarkRunner().run()

        delta = round(lace2_record.pass_rate - lace1_report.pass_rate, 4)
        regime_upgrade_confirmed = (
            lace2_record.benchmark_kind == "real_file_baseline"
            and lace1_report.benchmark_kind == "synthetic_baseline"
            and lace2_record.pass_rate >= lace1_report.pass_rate
        )

        return RegimeComparisonRecord(
            comparison_id=f"REGIME-CMP-{_ts()}",
            lace1_benchmark_kind=lace1_report.benchmark_kind,
            lace1_total_tasks=lace1_report.total_tasks,
            lace1_pass_rate=lace1_report.pass_rate,
            lace2_benchmark_kind=lace2_record.benchmark_kind,
            lace2_total_tasks=lace2_record.total_tasks,
            lace2_pass_rate=lace2_record.pass_rate,
            pass_rate_delta=delta,
            regime_upgrade_confirmed=regime_upgrade_confirmed,
            compared_at=_iso_now(),
        )

    def emit(self, record: RegimeComparisonRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "regime_comparison.json"
        out_path.write_text(
            json.dumps(asdict(record), indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["RegimeComparisonRecord", "BenchmarkRegimeComparator"]
