"""Consolidated local-autonomy dashboard artifact combining all major autonomy surfaces."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.aider_preflight import AiderPreflightResult
from framework.local_memory_store import LocalMemoryStore
from framework.repo_pattern_store import RepoPatternLibrary
from framework.retrieval_cache import RetrievalCache
from framework.retry_telemetry import RetryTelemetryRecord
from framework.task_class_readiness import TaskClassReadinessReport

# -- import-time assertions --
assert callable(LocalMemoryStore.read_successes), \
    "INTERFACE MISMATCH: LocalMemoryStore.read_successes"
assert callable(LocalMemoryStore.read_failures), \
    "INTERFACE MISMATCH: LocalMemoryStore.read_failures"
assert "entries" in RepoPatternLibrary.__dataclass_fields__, \
    "INTERFACE MISMATCH: RepoPatternLibrary.entries"
assert callable(RetrievalCache.get), \
    "INTERFACE MISMATCH: RetrievalCache.get"
assert "retry_eligible_failures" in RetryTelemetryRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: RetryTelemetryRecord.retry_eligible_failures"
assert "verdicts" in TaskClassReadinessReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassReadinessReport.verdicts"
assert "verdict" in AiderPreflightResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: AiderPreflightResult.verdict"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "local_autonomy_dashboard"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cache_entry_count(cache: RetrievalCache) -> int:
    cache_dir = getattr(cache, "_dir", None)
    if cache_dir is None:
        return 0
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return 0
    return len(list(cache_dir.glob("*.json")))


@dataclass
class LocalAutonomyDashboard:
    built_at: str
    memory_stats: dict
    repo_pattern_stats: dict
    retrieval_cache_stats: dict
    retry_telemetry_summary: dict
    readiness_summary: dict
    aider_preflight_summary: dict
    overall_health: str


def build_local_autonomy_dashboard(
    *,
    memory_store: LocalMemoryStore,
    pattern_library: RepoPatternLibrary,
    cache: RetrievalCache,
    retry_records: Optional[List[RetryTelemetryRecord]] = None,
    readiness_report: Optional[TaskClassReadinessReport] = None,
    preflight_result: Optional[AiderPreflightResult] = None,
) -> LocalAutonomyDashboard:
    retry_records = retry_records or []

    memory_stats = {
        "success_count": len(memory_store.read_successes()),
        "failure_count": len(memory_store.read_failures()),
    }

    repo_pattern_stats = {
        "total_patterns": len(pattern_library.entries),
        "top_task_kinds": list({e.task_kind for e in pattern_library.entries[:5]}),
    }

    retrieval_cache_stats = {
        "cache_dir": str(getattr(cache, "_dir", "unknown")),
        "entry_count": _cache_entry_count(cache),
    }

    retry_telemetry_summary = {
        "total_records": len(retry_records),
        "total_retry_eligible_failures": sum(
            r.retry_eligible_failures for r in retry_records
        ),
    }

    if readiness_report is not None:
        readiness_summary = {
            "overall_verdict": readiness_report.overall_verdict,
            "ready_count": readiness_report.ready_count,
            "marginal_count": readiness_report.marginal_count,
            "not_ready_count": readiness_report.not_ready_count,
        }
    else:
        readiness_summary = {"overall_verdict": "unknown", "ready_count": 0}

    if preflight_result is not None:
        aider_preflight_summary = {"verdict": preflight_result.verdict}
    else:
        aider_preflight_summary = {"verdict": "unknown"}

    # overall_health logic
    readiness_verdict = readiness_summary.get("overall_verdict", "unknown")
    preflight_verdict = aider_preflight_summary.get("verdict", "unknown")

    if readiness_report is None or preflight_result is None:
        overall_health = "unknown"
    elif readiness_verdict == "not_ready":
        overall_health = "degraded"
    elif memory_stats["failure_count"] > memory_stats["success_count"] and memory_stats["success_count"] > 0:
        overall_health = "degraded"
    elif readiness_verdict in ("ready", "marginal"):
        overall_health = "healthy"
    else:
        overall_health = "unknown"

    return LocalAutonomyDashboard(
        built_at=_iso_now(),
        memory_stats=memory_stats,
        repo_pattern_stats=repo_pattern_stats,
        retrieval_cache_stats=retrieval_cache_stats,
        retry_telemetry_summary=retry_telemetry_summary,
        readiness_summary=readiness_summary,
        aider_preflight_summary=aider_preflight_summary,
        overall_health=overall_health,
    )


def emit_dashboard(
    dashboard: LocalAutonomyDashboard,
    *,
    artifact_dir: Path = _DEFAULT_ARTIFACT_DIR,
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "local_autonomy_dashboard.json"
    out_path.write_text(
        json.dumps(
            {
                "built_at": dashboard.built_at,
                "overall_health": dashboard.overall_health,
                "memory_stats": dashboard.memory_stats,
                "repo_pattern_stats": dashboard.repo_pattern_stats,
                "retrieval_cache_stats": dashboard.retrieval_cache_stats,
                "retry_telemetry_summary": dashboard.retry_telemetry_summary,
                "readiness_summary": dashboard.readiness_summary,
                "aider_preflight_summary": dashboard.aider_preflight_summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = [
    "LocalAutonomyDashboard",
    "build_local_autonomy_dashboard",
    "emit_dashboard",
]
