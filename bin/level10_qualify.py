#!/usr/bin/env python3
"""Unified subsystem qualification report toward Level-10 targets."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest  # noqa: E402

DEFAULT_MANAGER4_TRACE = REPO_ROOT / "artifacts" / "manager4" / "traces.jsonl"
DEFAULT_MANAGER5_TRACE = REPO_ROOT / "artifacts" / "manager5" / "traces.jsonl"
DEFAULT_STAGE5_TRACE = REPO_ROOT / "artifacts" / "stage5_manager" / "traces.jsonl"
DEFAULT_RAG4_USAGE = REPO_ROOT / "artifacts" / "stage_rag4" / "usage.jsonl"
DEFAULT_MANAGER5_PLANS = REPO_ROOT / "artifacts" / "manager5" / "plans"


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def read_jsonl(path: Path, *, cutoff: datetime | None = None) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if cutoff is not None:
                ts = parse_timestamp(row.get("timestamp"))
                if ts is None or ts < cutoff:
                    continue
            rows.append(row)
    return rows


def summarize_candidate(manager4_rows: list[dict[str, Any]]) -> Counter:
    stats: Counter = Counter()
    for row in manager4_rows:
        if row.get("lane") != "candidate":
            continue
        if row.get("return_code") == 0:
            stats["success"] += 1
        else:
            stats["failure"] += 1
    return stats


def summarize_stage6(manager5_rows: list[dict[str, Any]]) -> Counter:
    stats: Counter = Counter()
    for row in manager5_rows:
        if row.get("lane") != "stage6":
            continue
        if row.get("return_code") == 0:
            stats["success"] += 1
        else:
            stats["failure"] += 1
    return stats


def summarize_worker(stage5_rows: list[dict[str, Any]]) -> Counter:
    stats: Counter = Counter()
    for row in stage5_rows:
        status = str(row.get("status") or "")
        if status == "success":
            stats["success"] += 1
        elif status == "failure":
            stats["failure"] += 1
    return stats


def summarize_rag4(rag4_rows: list[dict[str, Any]]) -> dict[str, Any]:
    plan_count = 0
    total_targets = 0
    confidence_sum = 0
    confidence_n = 0
    for row in rag4_rows:
        targets = row.get("targets") or []
        plan_count += 1
        total_targets += len(targets)
        for target in targets:
            confidence = target.get("confidence")
            if isinstance(confidence, (int, float)):
                confidence_sum += confidence
                confidence_n += 1
    avg_confidence = (confidence_sum / confidence_n) if confidence_n else 0.0
    return {
        "plans": plan_count,
        "targets": total_targets,
        "avg_confidence": round(avg_confidence, 3),
    }


def manager5_plan_lifecycle_health(plan_dir: Path) -> dict[str, Any]:
    if not plan_dir.exists():
        return {"plans": 0, "with_state": 0, "with_attempts": 0}
    plans = 0
    with_state = 0
    with_attempts = 0
    for path in sorted(plan_dir.glob("*.json")):
        plans += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("current_state"):
            with_state += 1
        if data.get("attempt_count"):
            with_attempts += 1
    return {"plans": plans, "with_state": with_state, "with_attempts": with_attempts}


def evaluate_subsystems(
    *,
    subsystem_levels: dict[str, Any],
    candidate_stats: Counter,
    stage6_stats: Counter,
    worker_stats: Counter,
    rag4_stats: dict[str, Any],
    lifecycle_stats: dict[str, Any],
    criteria: dict[str, Any],
    manifest_data: dict[str, Any],
) -> dict[str, Any]:
    candidate_success_threshold = int(criteria.get("candidate_success_threshold", 0))
    candidate_failure_budget = int(criteria.get("candidate_failure_budget", 0))
    stage6_success_threshold = int(criteria.get("stage6_success_threshold", 0))
    stage6_failure_budget = int(criteria.get("stage6_failure_budget", 0))
    required_candidate_pack = str(criteria.get("required_regression_pack") or "")
    required_preview_pack = str(criteria.get("required_preview_regression_pack") or "")

    candidate_pack_exists = bool(required_candidate_pack) and (REPO_ROOT / required_candidate_pack).exists()
    preview_pack_exists = bool(required_preview_pack) and (REPO_ROOT / required_preview_pack).exists()

    assessments: dict[str, Any] = {}

    def base_info(name: str) -> dict[str, Any]:
        data = subsystem_levels.get(name, {})
        return {
            "current_level": data.get("current_level"),
            "next_target_level": data.get("next_target_level"),
            "level10_definition": data.get("level10_definition"),
            "evidence_to_advance": data.get("evidence_to_advance", []),
        }

    stage_ok = stage6_stats["success"] >= stage6_success_threshold and stage6_stats["failure"] <= stage6_failure_budget
    assessments["stage_system"] = {
        **base_info("stage_system"),
        "evidence_met": stage_ok and preview_pack_exists,
        "evidence_snapshot": {
            "stage6_successes": stage6_stats["success"],
            "stage6_failures": stage6_stats["failure"],
            "stage6_success_threshold": stage6_success_threshold,
            "stage6_failure_budget": stage6_failure_budget,
            "required_preview_pack": required_preview_pack,
            "required_preview_pack_exists": preview_pack_exists,
        },
    }

    manager_ok = lifecycle_stats["with_state"] > 0 and lifecycle_stats["with_attempts"] > 0
    assessments["manager_system"] = {
        **base_info("manager_system"),
        "evidence_met": manager_ok,
        "evidence_snapshot": lifecycle_stats,
    }

    rag_ok = rag4_stats["plans"] > 0 and rag4_stats["avg_confidence"] >= 2.0
    assessments["rag_system"] = {
        **base_info("rag_system"),
        "evidence_met": rag_ok,
        "evidence_snapshot": rag4_stats,
    }

    promotion_ok = (
        candidate_stats["success"] >= candidate_success_threshold
        and candidate_stats["failure"] <= candidate_failure_budget
        and candidate_pack_exists
        and bool(subsystem_levels)
    )
    assessments["promotion_engine"] = {
        **base_info("promotion_engine"),
        "evidence_met": promotion_ok,
        "evidence_snapshot": {
            "candidate_successes": candidate_stats["success"],
            "candidate_failures": candidate_stats["failure"],
            "candidate_success_threshold": candidate_success_threshold,
            "candidate_failure_budget": candidate_failure_budget,
            "required_candidate_pack": required_candidate_pack,
            "required_candidate_pack_exists": candidate_pack_exists,
            "manifest_has_subsystem_policy": bool(subsystem_levels),
        },
    }

    worker_ok = worker_stats["success"] > 0 and worker_stats["failure"] <= max(1, candidate_failure_budget)
    assessments["worker_utilization"] = {
        **base_info("worker_utilization"),
        "evidence_met": worker_ok,
        "evidence_snapshot": {
            "worker_successes": worker_stats["success"],
            "worker_failures": worker_stats["failure"],
        },
    }

    lane_rules = manifest_data.get("lane_rules", {})
    regression_ok = candidate_pack_exists and preview_pack_exists and bool(lane_rules.get("candidate")) and bool(lane_rules.get("stage6"))
    assessments["regression_framework"] = {
        **base_info("regression_framework"),
        "evidence_met": regression_ok,
        "evidence_snapshot": {
            "candidate_pack_exists": candidate_pack_exists,
            "preview_pack_exists": preview_pack_exists,
            "candidate_rules_present": bool(lane_rules.get("candidate")),
            "stage6_rules_present": bool(lane_rules.get("stage6")),
        },
    }
    return assessments


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Level-10 readiness report")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--manager4-trace", default=str(DEFAULT_MANAGER4_TRACE))
    parser.add_argument("--manager5-trace", default=str(DEFAULT_MANAGER5_TRACE))
    parser.add_argument("--stage5-trace", default=str(DEFAULT_STAGE5_TRACE))
    parser.add_argument("--rag4-usage", default=str(DEFAULT_RAG4_USAGE))
    parser.add_argument("--manager5-plans", default=str(DEFAULT_MANAGER5_PLANS))
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest).resolve())
    criteria = manifest.data.get("promotion_policy", {}).get("criteria", {})
    trace_window_days = int(criteria.get("trace_window_days", 7))
    cutoff = datetime.now(UTC) - timedelta(days=trace_window_days)

    manager4_rows = list(read_jsonl(Path(args.manager4_trace).resolve(), cutoff=cutoff))
    manager5_rows = list(read_jsonl(Path(args.manager5_trace).resolve(), cutoff=cutoff))
    stage5_rows = list(read_jsonl(Path(args.stage5_trace).resolve(), cutoff=cutoff))
    rag4_rows = list(read_jsonl(Path(args.rag4_usage).resolve(), cutoff=cutoff))

    candidate_stats = summarize_candidate(manager4_rows)
    stage6_stats = summarize_stage6(manager5_rows)
    worker_stats = summarize_worker(stage5_rows)
    rag4_stats = summarize_rag4(rag4_rows)
    lifecycle_stats = manager5_plan_lifecycle_health(Path(args.manager5_plans).resolve())

    assessments = evaluate_subsystems(
        subsystem_levels=manifest.subsystem_levels,
        candidate_stats=candidate_stats,
        stage6_stats=stage6_stats,
        worker_stats=worker_stats,
        rag4_stats=rag4_stats,
        lifecycle_stats=lifecycle_stats,
        criteria=criteria,
        manifest_data=manifest.data,
    )

    lane_snapshot = {
        "production": manifest.data.get("lanes", {}).get("production", {}),
        "candidate": manifest.data.get("lanes", {}).get("candidate", {}),
        "preview": manifest.data.get("lanes", {}).get("stage6", {}),
    }
    summary = {
        "manifest_version": manifest.version,
        "trace_window_days": trace_window_days,
        "lane_snapshot": lane_snapshot,
        "metrics": {
            "candidate": dict(candidate_stats),
            "stage6_preview": dict(stage6_stats),
            "worker": dict(worker_stats),
            "rag4": rag4_stats,
            "manager5_lifecycle": lifecycle_stats,
        },
        "subsystem_assessments": assessments,
    }

    if args.json:
        json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    print(f"Manifest version: {summary['manifest_version']} | trace window: {trace_window_days}d")
    print("--- Lane snapshot ---")
    print(
        f"Production: {lane_snapshot['production'].get('stage_version')} "
        f"(status={lane_snapshot['production'].get('status')})"
    )
    print(
        f"Candidate: {lane_snapshot['candidate'].get('stage_version')} "
        f"(status={lane_snapshot['candidate'].get('status')})"
    )
    print(
        f"Preview: {lane_snapshot['preview'].get('stage_version')} "
        f"(status={lane_snapshot['preview'].get('status')})"
    )
    print("--- Metrics ---")
    print(
        f"Candidate jobs success/failure: {candidate_stats['success']}/{candidate_stats['failure']} | "
        f"Stage6 success/failure: {stage6_stats['success']}/{stage6_stats['failure']}"
    )
    print(
        f"Worker success/failure: {worker_stats['success']}/{worker_stats['failure']} | "
        f"RAG4 plans/targets: {rag4_stats['plans']}/{rag4_stats['targets']} (avg_conf={rag4_stats['avg_confidence']})"
    )
    print(
        f"Manager5 lifecycle plans with state/attempts: "
        f"{lifecycle_stats['with_state']}/{lifecycle_stats['plans']} "
        f"and {lifecycle_stats['with_attempts']}/{lifecycle_stats['plans']}"
    )
    print("--- Subsystem readiness ---")
    for name, item in assessments.items():
        status = "ready_for_next_level" if item["evidence_met"] else "needs_more_evidence"
        print(
            f"{name}: current={item['current_level']} next={item['next_target_level']} "
            f"status={status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
