"""LACE2-P11-FAILURE-MINER-SEAM-1: mine failures from benchmark, repair, and replay surfaces."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.lace2_benchmark_runner import Lace2BenchmarkRunner, Lace2BenchmarkRecord, TaskRunResult
from framework.repair_policy_proof import RepairPolicyProofRunner, RepairPolicyProofRecord
from framework.replay_proof import ReplayProofRunner, ReplayProofRecord

assert "passed" in TaskRunResult.__dataclass_fields__, "INTERFACE MISMATCH: TaskRunResult.passed"
assert "failure_reason" in TaskRunResult.__dataclass_fields__, "INTERFACE MISMATCH: TaskRunResult.failure_reason"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class FailureEntry:
    surface: str
    item_id: str
    failure_kind: str
    detail: Optional[str]


@dataclass
class FailureMinerRecord:
    miner_id: str
    benchmark_failures: int
    repair_mismatches: int
    replay_not_replayable: int
    total_failures: int
    failure_entries: List[FailureEntry]
    mined_at: str
    artifact_path: Optional[str] = None


class RealRunFailureMiner:
    """Mines failure signals from all three LACE2 live surfaces."""

    def mine(self) -> FailureMinerRecord:
        entries: List[FailureEntry] = []

        # Surface 1: benchmark task failures
        bench_record: Lace2BenchmarkRecord = Lace2BenchmarkRunner().run()
        for tr in bench_record.task_results:
            if not tr.passed:
                entries.append(FailureEntry(
                    surface="benchmark",
                    item_id=tr.task_id,
                    failure_kind=tr.failure_reason or "unknown",
                    detail=None,
                ))

        # Surface 2: repair policy decision mismatches
        repair_record: RepairPolicyProofRecord = RepairPolicyProofRunner().run()
        for row in repair_record.rows:
            if not row.matches_expected:
                entries.append(FailureEntry(
                    surface="repair_policy",
                    item_id=row.row_id,
                    failure_kind="decision_mismatch",
                    detail=f"expected={row.expected_action} actual={row.actual_action}",
                ))

        # Surface 3: replay gate not-replayable traces
        replay_record: ReplayProofRecord = ReplayProofRunner().run()
        for row in replay_record.rows:
            if not row.replayable:
                entries.append(FailureEntry(
                    surface="replay_gate",
                    item_id=row.trace_id,
                    failure_kind="not_replayable",
                    detail=row.not_replayable_reason,
                ))

        bench_failures = sum(1 for e in entries if e.surface == "benchmark")
        repair_mismatches = sum(1 for e in entries if e.surface == "repair_policy")
        replay_not_replayable = sum(1 for e in entries if e.surface == "replay_gate")

        return FailureMinerRecord(
            miner_id=f"FAIL-MINE-{_ts()}",
            benchmark_failures=bench_failures,
            repair_mismatches=repair_mismatches,
            replay_not_replayable=replay_not_replayable,
            total_failures=len(entries),
            failure_entries=entries,
            mined_at=_iso_now(),
        )

    def emit(self, record: FailureMinerRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "failure_miner_report.json"
        out_path.write_text(
            json.dumps({
                "miner_id": record.miner_id,
                "benchmark_failures": record.benchmark_failures,
                "repair_mismatches": record.repair_mismatches,
                "replay_not_replayable": record.replay_not_replayable,
                "total_failures": record.total_failures,
                "failure_entries": [asdict(e) for e in record.failure_entries],
                "mined_at": record.mined_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["FailureEntry", "FailureMinerRecord", "RealRunFailureMiner"]
