"""FailureClusterAnalyzer: groups recurring local failures into actionable categories."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from framework.local_memory_store import LocalMemoryStore, FailurePattern

# -- import-time assertions --
assert "task_kind" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.task_kind"
assert "error_type" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.error_type"
assert "error_summary" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.error_summary"
assert callable(getattr(LocalMemoryStore, "read_failures", None)), \
    "INTERFACE MISMATCH: LocalMemoryStore.read_failures"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cluster_key(failure: FailurePattern) -> str:
    et = (failure.error_type or "unknown").strip()[:40]
    tk = (failure.task_kind or "unknown").strip()[:30]
    # Normalize error summary prefix (first 30 chars)
    prefix = (failure.error_summary or "")[:30].strip()
    return f"{tk}|{et}|{prefix}"


@dataclass(frozen=True)
class FailureCluster:
    cluster_key: str
    task_kind: str
    error_type: str
    error_prefix: str
    occurrence_count: int
    example_summary: str


@dataclass
class FailureClusterReport:
    clusters: List[FailureCluster]
    total_failures_analyzed: int
    top_cluster_key: Optional[str]
    analyzed_at: str


class FailureClusterAnalyzer:
    """Groups failure patterns by task_kind + error_type + normalized prefix."""

    def __init__(self, *, memory_store: Optional[LocalMemoryStore] = None):
        self._memory_store = memory_store or LocalMemoryStore()

    def analyze(self) -> FailureClusterReport:
        try:
            failures: List[FailurePattern] = self._memory_store.read_failures()
        except Exception:
            failures = []

        cluster_map: Dict[str, List[FailurePattern]] = {}
        for f in failures:
            key = _cluster_key(f)
            cluster_map.setdefault(key, []).append(f)

        clusters = []
        for key, group in sorted(cluster_map.items(), key=lambda x: -len(x[1])):
            rep = group[0]
            clusters.append(FailureCluster(
                cluster_key=key,
                task_kind=rep.task_kind or "unknown",
                error_type=rep.error_type or "unknown",
                error_prefix=(rep.error_summary or "")[:30],
                occurrence_count=len(group),
                example_summary=rep.error_summary or "",
            ))

        top_key = clusters[0].cluster_key if clusters else None
        return FailureClusterReport(
            clusters=clusters,
            total_failures_analyzed=len(failures),
            top_cluster_key=top_key,
            analyzed_at=_iso_now(),
        )


def emit_failure_clusters(
    report: FailureClusterReport,
    *,
    artifact_dir: Path = Path("artifacts") / "failure_clusters",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "failure_cluster_report.json"
    out_path.write_text(
        json.dumps(
            {
                "total_failures_analyzed": report.total_failures_analyzed,
                "top_cluster_key": report.top_cluster_key,
                "cluster_count": len(report.clusters),
                "analyzed_at": report.analyzed_at,
                "clusters": [
                    {
                        "cluster_key": c.cluster_key,
                        "task_kind": c.task_kind,
                        "error_type": c.error_type,
                        "occurrence_count": c.occurrence_count,
                        "example_summary": c.example_summary[:100],
                    }
                    for c in report.clusters[:10]
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["FailureCluster", "FailureClusterReport", "FailureClusterAnalyzer", "emit_failure_clusters"]
