#!/usr/bin/env python3
"""Unified subsystem qualification report toward Level-10 targets."""

from __future__ import annotations  # stage6-grouped

import argparse  # stage7-op  # stage6-rag4-v3
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from _datetime_compat import UTC
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest  # noqa: E402

DEFAULT_MANAGER4_TRACE = REPO_ROOT / "artifacts" / "manager4" / "traces.jsonl"
DEFAULT_MANAGER5_TRACE = REPO_ROOT / "artifacts" / "manager5" / "traces.jsonl"
DEFAULT_MANAGER6_TRACE = REPO_ROOT / "artifacts" / "manager6" / "traces.jsonl"
DEFAULT_STAGE5_TRACE = REPO_ROOT / "artifacts" / "stage5_manager" / "traces.jsonl"
DEFAULT_RAG4_USAGE = REPO_ROOT / "artifacts" / "stage_rag4" / "usage.jsonl"
DEFAULT_RAG6_USAGE = REPO_ROOT / "artifacts" / "stage_rag6" / "usage.jsonl"
DEFAULT_STAGE3_TRACE = REPO_ROOT / "artifacts" / "stage3_manager" / "traces.jsonl"
DEFAULT_MANAGER5_PLANS = REPO_ROOT / "artifacts" / "manager5" / "plans"
QUAL_HISTORY = REPO_ROOT / "artifacts" / "promotion" / "qualification_history.jsonl"


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


def filter_by_manifest_version(
    rows: list[dict[str, Any]],
    *,
    manifest_version: int,
    strict: bool,
) -> tuple[list[dict[str, Any]], int]:
    filtered: list[dict[str, Any]] = []
    dropped = 0
    for row in rows:
        row_version = row.get("manifest_version")
        if row_version is None:
            if strict:
                dropped += 1
                continue
            filtered.append(row)
            continue
        if int(row_version) != manifest_version:
            dropped += 1
            continue
        filtered.append(row)
    return filtered, dropped


def candidate_run_key(row: dict[str, Any]) -> str:
    extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
    commit_msg = str(extra.get("commit_msg") or "")
    target = ""
    targets = row.get("targets")
    if isinstance(targets, list) and targets:
        target = str(targets[0])
    if not target:
        target = str(row.get("target") or "")
    secondary_target = str(extra.get("secondary_target") or "")
    if commit_msg and target:
        # Batch files change across retries; logical run identity should not.
        return f"task:{commit_msg}|target:{target}|secondary:{secondary_target}"
    batch_file = extra.get("batch_file") or row.get("batch_file")
    if batch_file:
        return f"batch:{batch_file}"
    return f"target:{target}|commit:{commit_msg}"


def latest_candidate_rows(manager4_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_rows: dict[str, dict[str, Any]] = {}
    for row in manager4_rows:
        if row.get("lane") != "candidate":
            continue
        key = candidate_run_key(row)
        ts = parse_timestamp(row.get("timestamp")) or datetime.min.replace(tzinfo=UTC)
        previous = latest_rows.get(key)
        if previous is None:
            latest_rows[key] = row
            continue
        prev_ts = parse_timestamp(previous.get("timestamp")) or datetime.min.replace(tzinfo=UTC)
        if ts >= prev_ts:
            latest_rows[key] = row
    return sorted(
        latest_rows.values(),
        key=lambda row: parse_timestamp(row.get("timestamp")) or datetime.min.replace(tzinfo=UTC),
    )


def summarize_candidate(manager4_rows: list[dict[str, Any]]) -> Counter:
    latest_rows = latest_candidate_rows(manager4_rows)
    stats: Counter = Counter()
    for row in latest_rows:
        if row.get("return_code") == 0:
            stats["success"] += 1
        else:
            stats["failure"] += 1
    return stats


def summarize_candidate_recovery(manager4_rows: list[dict[str, Any]]) -> dict[str, int]:
    latest_rows = latest_candidate_rows(manager4_rows)
    success_streak = 0
    for row in reversed(latest_rows):
        if row.get("return_code") == 0:
            success_streak += 1
            continue
        break
    return {
        "latest_success_streak": success_streak,
        "latest_run_count": len(latest_rows),
    }


def summarize_stage6(manager5_rows: list[dict[str, Any]]) -> Counter:
    def stage6_run_key(row: dict[str, Any]) -> str:
        extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
        plan_id = extra.get("plan_id")
        if plan_id:
            return f"plan:{plan_id}"
        return f"timestamp:{row.get('timestamp')}"

    latest_rows: dict[str, dict[str, Any]] = {}
    for row in manager5_rows:
        if row.get("lane") != "stage6":
            continue
        key = stage6_run_key(row)
        ts = parse_timestamp(row.get("timestamp")) or datetime.min.replace(tzinfo=UTC)
        previous = latest_rows.get(key)
        if previous is None:
            latest_rows[key] = row
            continue
        prev_ts = parse_timestamp(previous.get("timestamp")) or datetime.min.replace(tzinfo=UTC)
        if ts >= prev_ts:
            latest_rows[key] = row

    stats: Counter = Counter()
    for row in latest_rows.values():
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


def summarize_stage8(manager6_rows: list[dict[str, Any]]) -> dict[str, Any]:
    resumed = 0
    paused = 0
    checkpointed = 0
    rollback_contracts = 0
    executed = 0
    worker_budget_decisions = 0
    worker_budget_adaptive_decisions = 0
    worker_budget_deferred = 0
    worker_budget_manual_hints = 0
    manager_strategy_decisions = 0
    for row in manager6_rows:
        stage_version = str(row.get("stage_version") or "")
        if not stage_version.startswith("stage8"):
            continue
        extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
        if extra.get("resume"):
            resumed += 1
        if row.get("promotion_outcome") == "paused":
            paused += 1
        if extra.get("checkpoint_path"):
            checkpointed += 1
        if isinstance(extra.get("manager_decisions"), dict):
            manager_strategy_decisions += 1
        for sub in extra.get("subplans", []) or []:
            if not isinstance(sub, dict):
                continue
            budget_decision = sub.get("worker_budget_decision")
            if budget_decision:
                worker_budget_decisions += 1
                if isinstance(budget_decision, dict):
                    if int(budget_decision.get("adaptive_adjustment") or 0) != 0:
                        worker_budget_adaptive_decisions += 1
            status = str(sub.get("status") or "")
            if status == "deferred_worker_budget":
                worker_budget_deferred += 1
            if str(sub.get("escalation_hint") or "").startswith("manual_"):
                worker_budget_manual_hints += 1
            if sub.get("status") in {"success", "failure", "partial_success", "dropped_preflight"}:
                executed += 1
                if isinstance(sub.get("rollback_contract"), dict) and sub["rollback_contract"].get("contract_version"):
                    rollback_contracts += 1
    rollback_coverage = (rollback_contracts / executed) if executed else 0.0
    return {
        "resumed_runs": resumed,
        "paused_runs": paused,
        "checkpointed_runs": checkpointed,
        "executed_subplans": executed,
        "rollback_contract_coverage": round(rollback_coverage, 3),
        "worker_budget_decisions": worker_budget_decisions,
        "worker_budget_adaptive_decisions": worker_budget_adaptive_decisions,
        "worker_budget_deferred_subplans": worker_budget_deferred,
        "worker_budget_manual_hints": worker_budget_manual_hints,
        "manager_strategy_decision_rows": manager_strategy_decisions,
    }


def summarize_rag6(rag6_rows: list[dict[str, Any]]) -> dict[str, Any]:
    plans = len(rag6_rows)
    clusters = 0
    with_risk = 0
    with_yield = 0
    for row in rag6_rows:
        subplans = row.get("subplans", []) or []
        clusters += len(subplans)
        for sub in subplans:
            if not isinstance(sub, dict):
                continue
            if "risk_score" in sub and "conflict_signals" in sub:
                with_risk += 1
            if "yield_score" in sub:
                with_yield += 1
    return {
        "plans": plans,
        "clusters": clusters,
        "clusters_with_risk": with_risk,
        "clusters_with_yield": with_yield,
    }


def summarize_gate_chain(entries: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(entries)
    if total == 0:
        return {
            "total": 0,
            "accepted": 0,
            "rejected": 0,
            "fully_qualified": 0,
            "qualified_smoke_fallback": 0,
            "qualified_partial_gates": 0,
            "qualification_rate": 0.0,
            "full_qualification_rate": 0.0,
            "gate_coverage": {
                "g1_syntax": 0,
                "g2_tests": 0,
                "g3_repo_check": 0,
                "g4_repo_quick": 0,
            },
            "discovery_mode_distribution": {},
            "classification_distribution": {},
        }
    accepted = [e for e in entries if e.get("accepted")]
    rejected = [e for e in entries if not e.get("accepted")]
    fully_qualified = [
        e for e in accepted
        if len(e.get("gates_run", [])) == 4
        and e.get("target_test_discovery_mode") not in ("none", "skipped", None)
    ]
    qualified_smoke = [
        e for e in accepted
        if len(e.get("gates_run", [])) == 4
        and e.get("target_test_discovery_mode") == "none"
    ]
    qualified_partial = [e for e in accepted if len(e.get("gates_run", [])) < 4]
    return {
        "total": total,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "fully_qualified": len(fully_qualified),
        "qualified_smoke_fallback": len(qualified_smoke),
        "qualified_partial_gates": len(qualified_partial),
        "qualification_rate": round(len(accepted) / total, 3),
        "full_qualification_rate": round(len(fully_qualified) / total, 3),
        "gate_coverage": {
            "g1_syntax": sum(1 for e in entries if "g1_syntax" in e.get("gates_run", [])),
            "g2_tests": sum(1 for e in entries if "g2_tests" in e.get("gates_run", [])),
            "g3_repo_check": sum(1 for e in entries if "g3_repo_check" in e.get("gates_run", [])),
            "g4_repo_quick": sum(1 for e in entries if "g4_repo_quick" in e.get("gates_run", [])),
        },
        "discovery_mode_distribution": dict(Counter(
            e.get("target_test_discovery_mode", "skipped") for e in accepted
        )),
        "classification_distribution": dict(Counter(
            e.get("classification", "unknown") for e in entries
        )),
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
    candidate_recovery: dict[str, int],
    lifecycle_stats: dict[str, Any],
    gate_chain_stats: dict[str, Any],
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
        alias = {
            "regression_framework": "regression_qualification_framework",
        }
        data = subsystem_levels.get(name) or subsystem_levels.get(alias.get(name, ""), {})
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
            "latest_candidate_success_streak": int(candidate_recovery.get("latest_success_streak", 0)),
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
    gate_chain_threshold = float(criteria.get("gate_chain_min_full_qualification_rate", 0.5))
    gate_chain_ok = (
        gate_chain_stats.get("total", 0) > 0
        and gate_chain_stats.get("full_qualification_rate", 0.0) >= gate_chain_threshold
        and gate_chain_stats.get("gate_coverage", {}).get("g4_repo_quick", 0) > 0
    )
    assessments["gate_chain"] = {
        **base_info("gate_chain"),
        "evidence_met": gate_chain_ok,
        "evidence_snapshot": {
            "total": gate_chain_stats.get("total", 0),
            "accepted": gate_chain_stats.get("accepted", 0),
            "full_qualification_rate": gate_chain_stats.get("full_qualification_rate", 0.0),
            "gate_coverage_g4_repo_quick": gate_chain_stats.get("gate_coverage", {}).get("g4_repo_quick", 0),
            "threshold": gate_chain_threshold,
        },
    }
    return assessments


def evaluate_v8_gates(
    *,
    manifest_data: dict[str, Any],
    stage8_stats: dict[str, Any],
    rag6_stats: dict[str, Any],
    assessments: dict[str, Any],
    gate_chain_stats: dict[str, Any],
) -> dict[str, Any]:
    v8 = manifest_data.get("version8_upgrade_list", {})
    stage_gate = (
        stage8_stats.get("resumed_runs", 0) > 0
        and stage8_stats.get("checkpointed_runs", 0) > 0
        and stage8_stats.get("rollback_contract_coverage", 0.0) >= 1.0
    )
    manager_gate = (
        stage8_stats.get("manager_strategy_decision_rows", 0) > 0
        and assessments.get("manager_system", {}).get("evidence_met", False)
    )
    rag_gate = (
        rag6_stats.get("plans", 0) > 0
        and rag6_stats.get("clusters", 0) > 0
        and rag6_stats.get("clusters_with_risk", 0) >= 1
        and rag6_stats.get("clusters_with_yield", 0) >= 1
    )
    worker_gate = stage8_stats.get("worker_budget_decisions", 0) > 0
    promotion_gate = bool(v8) and bool(assessments.get("promotion_engine", {}).get("evidence_met"))
    regression_gate = (
        bool(assessments.get("regression_framework", {}).get("evidence_met"))
        and bool(v8)
    )
    gate_chain_threshold = float(
        manifest_data.get("promotion_policy", {})
        .get("criteria", {})
        .get("gate_chain_min_full_qualification_rate", 0.5)
    )
    gate_chain_ready = (
        gate_chain_stats.get("total", 0) > 0
        and gate_chain_stats.get("full_qualification_rate", 0.0) >= gate_chain_threshold
        and gate_chain_stats.get("gate_coverage", {}).get("g4_repo_quick", 0) > 0
    )
    gates = {
        "stage8_ready": stage_gate,
        "manager8_ready": manager_gate,
        "rag8_ready": rag_gate,
        "worker8_ready": worker_gate,
        "promotion8_ready": promotion_gate,
        "qualification8_ready": regression_gate,
        "gate_chain_ready": gate_chain_ready,
    }
    return {
        "gates": gates,
        "all_ready": all(gates.values()),
        "missing": [name for name, ok in gates.items() if not ok],
    }


def append_qualification_history(payload: dict[str, Any]) -> None:
    QUAL_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with QUAL_HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Level-10 readiness report")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH) )
    parser.add_argument("--manager4-trace", default=str(DEFAULT_MANAGER4_TRACE))
    parser.add_argument("--manager5-trace", default=str(DEFAULT_MANAGER5_TRACE))
    parser.add_argument("--manager6-trace", default=str(DEFAULT_MANAGER6_TRACE))
    parser.add_argument("--stage5-trace", default=str(DEFAULT_STAGE5_TRACE))
    parser.add_argument("--rag4-usage", default=str(DEFAULT_RAG4_USAGE))
    parser.add_argument("--rag6-usage", default=str(DEFAULT_RAG6_USAGE))
    parser.add_argument("--manager5-plans", default=str(DEFAULT_MANAGER5_PLANS))
    parser.add_argument("--stage3-trace", default=str(DEFAULT_STAGE3_TRACE))
    parser.add_argument(
        "--strict-manifest-version",
        action="store_true",
        help="Only count trace rows that match the current manifest version",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    parser.add_argument(
        "--fail-on-incomplete-v8-gates",
        action="store_true",
        help="Exit 1 if v8_gate_assertions.all_ready is False",
    )
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest).resolve())
    manifest_version = manifest.version
    criteria = manifest.data.get("promotion_policy", {}).get("criteria", {})
    trace_window_days = int(criteria.get("trace_window_days", 7))
    cutoff = datetime.now(UTC) - timedelta(days=trace_window_days)

    manager4_all = list(read_jsonl(Path(args.manager4_trace).resolve(), cutoff=cutoff))
    manager5_all = list(read_jsonl(Path(args.manager5_trace).resolve(), cutoff=cutoff))
    manager6_rows = list(read_jsonl(Path(args.manager6_trace).resolve(), cutoff=cutoff))
    stage5_rows = list(read_jsonl(Path(args.stage5_trace).resolve(), cutoff=cutoff))
    rag4_rows = list(read_jsonl(Path(args.rag4_usage).resolve(), cutoff=cutoff))
    rag6_rows = list(read_jsonl(Path(args.rag6_usage).resolve(), cutoff=cutoff))
    stage3_rows = list(read_jsonl(Path(args.stage3_trace).resolve()))
    manager4_rows, manager4_dropped = filter_by_manifest_version(
        manager4_all,
        manifest_version=manifest_version,
        strict=bool(args.strict_manifest_version),
    )
    manager5_rows, manager5_dropped = filter_by_manifest_version(
        manager5_all,
        manifest_version=manifest_version,
        strict=bool(args.strict_manifest_version),
    )

    candidate_stats = summarize_candidate(manager4_rows)
    candidate_recovery = summarize_candidate_recovery(manager4_rows)
    stage6_stats = summarize_stage6(manager5_rows)
    worker_stats = summarize_worker(stage5_rows)
    rag4_stats = summarize_rag4(rag4_rows)
    stage8_stats = summarize_stage8(manager6_rows)
    rag6_stats = summarize_rag6(rag6_rows)
    lifecycle_stats = manager5_plan_lifecycle_health(Path(args.manager5_plans).resolve())
    gate_chain_stats = summarize_gate_chain(stage3_rows)

    assessments = evaluate_subsystems(
        subsystem_levels=manifest.subsystem_levels,
        candidate_stats=candidate_stats,
        stage6_stats=stage6_stats,
        worker_stats=worker_stats,
        rag4_stats=rag4_stats,
        candidate_recovery=candidate_recovery,
        lifecycle_stats=lifecycle_stats,
        gate_chain_stats=gate_chain_stats,
        criteria=criteria,
        manifest_data=manifest.data,
    )
    v8_assertions = evaluate_v8_gates(
        manifest_data=manifest.data,
        stage8_stats=stage8_stats,
        rag6_stats=rag6_stats,
        assessments=assessments,
        gate_chain_stats=gate_chain_stats,
    )

    lane_snapshot = {
        "production": manifest.data.get("lanes", {}).get("production", {}),
        "candidate": manifest.data.get("lanes", {}).get("candidate", {}),
        "preview": manifest.data.get("lanes", {}).get("stage6", {}),
    }
    summary = {
        "manifest_version": manifest_version,
        "trace_window_days": trace_window_days,
        "trace_filter": {
            "strict_manifest_version": bool(args.strict_manifest_version),
            "manager4_rows_total": len(manager4_all),
            "manager4_rows_kept": len(manager4_rows),
            "manager4_rows_dropped": manager4_dropped,
            "manager5_rows_total": len(manager5_all),
            "manager5_rows_kept": len(manager5_rows),
            "manager5_rows_dropped": manager5_dropped,
        },
        "lane_snapshot": lane_snapshot,
        "metrics": {
            "candidate": dict(candidate_stats),
            "candidate_recovery": candidate_recovery,
            "stage6_preview": dict(stage6_stats),
            "worker": dict(worker_stats),
            "rag4": rag4_stats,
            "stage8": stage8_stats,
            "rag6": rag6_stats,
            "manager5_lifecycle": lifecycle_stats,
            "gate_chain": gate_chain_stats,
        },
        "subsystem_assessments": assessments,
        "v8_gate_assertions": v8_assertions,
    }

    append_qualification_history(
        {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "manifest_version": manifest_version,
            "trace_window_days": trace_window_days,
            "metrics": summary["metrics"],
            "v8_gate_assertions": v8_assertions,
            "subsystem_assessments": assessments,
        }
    )

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
    print("--- Gate chain ---")
    print(
        f"Stage3 gate chain: {gate_chain_stats['accepted']}/{gate_chain_stats['total']} accepted "
        f"| fully_qualified={gate_chain_stats['fully_qualified']} "
        f"| full_qualification_rate={gate_chain_stats['full_qualification_rate']}"
    )
    print("--- V8 gate assertions ---")
    gca = v8_assertions["gates"]
    print(
        f"gate_chain_ready={gca.get('gate_chain_ready')} | "
        f"all_ready={v8_assertions['all_ready']}"
    )
    if v8_assertions["missing"]:
        print(f"missing gates: {', '.join(v8_assertions['missing'])}")
    if args.fail_on_incomplete_v8_gates and not v8_assertions.get("all_ready", False):
        missing = v8_assertions.get("missing", [])
        print(
            f"[qualify] FAIL: v8 gates incomplete — missing: {', '.join(missing) or 'unknown'}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
