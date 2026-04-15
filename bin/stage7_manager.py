#!/usr/bin/env python3
"""Manager-9 orchestrator for Stage-7/8 multi-plan execution."""

from __future__ import annotations

import argparse  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
from promotion.worker_budget import (
    WorkerBudgetDecision,
    apply_worker_budget,
    record_worker_outcome,
    summarize_worker_family_outcomes,
    worker_budget_forecast,
)
from promotion.tracing import PromotionTraceEntry, append_trace, current_commit_hash

STAGE6_MANAGER = REPO_ROOT / "bin" / "stage6_manager.py"
STAGE_RAG6_PLAN = REPO_ROOT / "bin" / "stage_rag6_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "manager6"
QUAL_HISTORY_PATH = REPO_ROOT / "artifacts" / "promotion" / "qualification_history.jsonl"
LEARNING_LATEST_PATH = REPO_ROOT / "artifacts" / "codex51" / "learning" / "latest.json"
DEFAULT_MANAGER6_HISTORY_WINDOW_DAYS = 14
IMPORT_BASE_RE = re.compile(r"^(import|from)\s+")
SHELL_STRICT_RE = re.compile(r"^\s*set -euo pipefail\s*$")
SHELL_ASSIGNMENT_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*=")
SHELL_PRINT_RE = re.compile(r"^\s*(echo|printf)\b")
SHELL_RISKY_TOKEN_RE = re.compile(
    r"(\b(set|if|then|fi|elif|else|for|while|until|case|esac|do|done|exit|return|trap)\b|set\s*-[A-Za-z]+)",
    re.IGNORECASE,
)


def plan_history_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / f"{plan_id}.json"


def plan_checkpoint_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / plan_id / "checkpoints.json"


def write_plan_history(plan_id: str, payload: dict[str, Any]) -> None:
    history_path = plan_history_path(plan_id)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if history_path.exists():
        try:
            existing = json.loads(history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    history = existing.get("history", [])
    event = dict(payload)
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    history.append(event)

    plan_payload: dict[str, Any] = existing.get("plan_payload", {})
    plan_payload.update(payload.get("plan_payload", {}))

    merged = {
        "plan_id": plan_id,
        "plan_payload": plan_payload,
        "history": history,
        "current_state": payload.get("state") or existing.get("current_state"),
        "last_updated": event["timestamp"],
    }
    history_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def load_plan_history(plan_id: str) -> dict[str, Any]:
    history_path = plan_history_path(plan_id)
    if not history_path.exists():
        return {}
    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_checkpoints(plan_id: str) -> dict[str, Any]:
    path = plan_checkpoint_path(plan_id)
    if not path.exists():
        return {"plan_id": plan_id, "subplans": {}, "updated_at": None}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.setdefault("plan_id", plan_id)
            payload.setdefault("subplans", {})
            return payload
    except json.JSONDecodeError:
        pass
    return {"plan_id": plan_id, "subplans": {}, "updated_at": None}


def save_checkpoint(plan_id: str, status: dict[str, Any], *, attempt_index: int) -> None:
    checkpoint = load_checkpoints(plan_id)
    subplans = checkpoint.setdefault("subplans", {})
    subplan_id = str(status.get("subplan_id") or f"subplan-{len(subplans) + 1}")
    record = dict(status)
    record["attempt_index"] = int(attempt_index)
    record["checkpointed_at"] = datetime.now(timezone.utc).isoformat()
    subplans[subplan_id] = record
    checkpoint["updated_at"] = record["checkpointed_at"]
    path = plan_checkpoint_path(plan_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_resume_complete_status(status: str) -> bool:
    return status in {"success", "partial_success", "dropped_preflight"}


def _sorted_targets(value: Any) -> list[str]:
    return sorted({str(item) for item in (value or []) if item})


def _is_dispatch_status(status: str) -> bool:
    return status in {"success", "failure", "partial_success"}


def _is_no_dispatch_status(status: str) -> bool:
    return status in {
        "dropped_preflight",
        "deferred_worker_budget",
        "deferred_manager_policy",
        "dropped_family_budget",
        "resumed_skip_completed",
    }


def _verify_rollback_contract_for_status(status: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    contract = status.get("rollback_contract")
    if not isinstance(contract, dict):
        return {"ok": False, "issues": ["missing_rollback_contract"], "dispatch": False}

    version = str(contract.get("contract_version") or "")
    if version != "stage9-v1":
        issues.append("rollback_contract_version_mismatch")

    strategy = str(contract.get("strategy") or "")
    if not strategy:
        issues.append("rollback_strategy_missing")

    trigger = contract.get("trigger_on_failure")
    if not isinstance(trigger, bool):
        issues.append("rollback_trigger_not_bool")

    verification = str(contract.get("verification") or "")
    if not verification:
        issues.append("rollback_verification_missing")

    scope = _sorted_targets(contract.get("rollback_scope"))
    targets = _sorted_targets(status.get("targets"))
    status_name = str(status.get("status") or "")
    dispatch = _is_dispatch_status(status_name)
    no_dispatch = _is_no_dispatch_status(status_name)

    if dispatch:
        if scope != targets:
            issues.append("rollback_scope_mismatch_dispatch")
        expected_trigger = int(status.get("return_code") or 0) != 0
        if trigger is not expected_trigger:
            issues.append("rollback_trigger_mismatch_dispatch")
        if verification != "stage6_return_code":
            issues.append("rollback_verification_mismatch_dispatch")
    elif no_dispatch:
        if scope:
            issues.append("rollback_scope_nonempty_no_dispatch")
        if trigger is not False:
            issues.append("rollback_trigger_mismatch_no_dispatch")
        if verification != "not_applicable_no_dispatch":
            issues.append("rollback_verification_mismatch_no_dispatch")
    else:
        issues.append("rollback_unknown_status_class")

    return {"ok": not issues, "issues": issues, "dispatch": dispatch}


def _validate_resume_checkpoint_for_subplan(subplan: dict[str, Any], prior: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    prior_status = str(prior.get("status") or "")
    if not _is_resume_complete_status(prior_status):
        issues.append("resume_status_not_complete")
    if not str(prior.get("checkpointed_at") or ""):
        issues.append("checkpoint_timestamp_missing")
    if int(prior.get("attempt_index") or 0) <= 0:
        issues.append("checkpoint_attempt_index_invalid")

    expected_targets = _sorted_targets(subplan.get("targets"))
    prior_targets = _sorted_targets(prior.get("targets"))
    if expected_targets != prior_targets:
        issues.append("checkpoint_targets_mismatch")

    verification = _verify_rollback_contract_for_status(prior)
    if not verification.get("ok"):
        issues.extend([f"checkpoint_{issue}" for issue in verification.get("issues", [])])
    return (not issues, issues)


def _subplan_coverage_summary(subplans: list[dict[str, Any]], statuses: list[dict[str, Any]]) -> dict[str, Any]:
    expected_ids = [str(sp.get("subplan_id") or "") for sp in subplans if str(sp.get("subplan_id") or "")]
    accounted: set[str] = set()
    for row in statuses:
        sid = str(row.get("subplan_id") or "")
        if sid in expected_ids:
            accounted.add(sid)
            continue
        for exp in expected_ids:
            # Account for derived subplan identifiers emitted by bounded fallback paths.
            if sid.startswith(f"{exp}-split-") or sid.startswith(f"{exp}-manager14-"):
                accounted.add(exp)
                break
    missing = sorted([sid for sid in expected_ids if sid and sid not in accounted])
    return {
        "expected_subplans": len(expected_ids),
        "accounted_subplans": len(accounted),
        "missing_subplans": missing,
        "coverage_ok": not missing,
    }


def _subplan_family_key(subplan: dict[str, Any]) -> str:
    meta = subplan.get("target_meta") or []
    families = sorted({str(item.get("family") or "") for item in meta if item.get("family")})
    if families:
        return ",".join(families)
    targets = [str(t) for t in subplan.get("targets", []) if t]
    if not targets:
        return "unknown"
    stems = sorted({Path(t).stem.split("_")[0] for t in targets})
    return ",".join(stems) if stems else "unknown"


def _infer_task_class_from_query(query: str) -> str:
    q = query.lower()
    if any(token in q for token in ("resume", "checkpoint", "reconcile", "rollback")):
        return "resumable_checkpointed"
    if any(token in q for token in ("rag", "retrieval", "ranking", "cluster")):
        return "retrieval_orchestration"
    if any(token in q for token in ("stage", "manager", "orchestration")):
        return "multi_file_orchestration"
    if any(token in q for token in ("contract", "literal", "shell", "script")):
        return "safe_contracts"
    return "bounded_architecture"


def _subplan_complexity(subplan: dict[str, Any]) -> str:
    targets = [str(t) for t in subplan.get("targets", []) if t]
    risk_score = float(subplan.get("risk_score") or 0.0)
    if len(targets) >= 3 or risk_score >= 0.6:
        return "high"
    if len(targets) >= 2 or risk_score >= 0.3:
        return "medium"
    return "low"


def _resolve_worker_budget_limits(
    *,
    manifest_data: dict[str, Any],
    worker_budget_profile: str,
    task_class: str,
    complexity: str,
    learning_priors: dict[str, Any],
    grouped_limit: int,
    single_limit: int,
) -> dict[str, Any]:
    profiles = manifest_data.get("worker_budget_profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    selected_profile = "default"
    class_key = task_class if task_class in profiles else "default"
    if worker_budget_profile != "auto" and worker_budget_profile in profiles:
        class_key = worker_budget_profile
    profile_payload = profiles.get(class_key) if isinstance(profiles.get(class_key), dict) else {}
    if profile_payload:
        selected_profile = class_key

    base_grouped = int(profile_payload.get("grouped_limit", grouped_limit) or grouped_limit)
    base_single = int(profile_payload.get("single_limit", single_limit) or single_limit)
    multipliers = profile_payload.get("complexity_multipliers")
    if not isinstance(multipliers, dict):
        multipliers = {}
    multiplier = float(multipliers.get(complexity, 1.0) or 1.0)
    effective_grouped = max(1, int(round(base_grouped * multiplier)))
    effective_single = max(1, int(round(base_single * multiplier)))

    learning_adjust_grouped = 0
    learning_adjust_single = 0
    learning_reason = "none"
    if bool(learning_priors.get("active")):
        weak_classes = {str(item) for item in (learning_priors.get("weak_classes") or []) if item}
        recurrence_pressure = bool(learning_priors.get("recurrence_pressure"))
        benchmark_escalation = float(learning_priors.get("benchmark_escalation_rate") or 0.0)
        benchmark_quality = float(learning_priors.get("benchmark_first_attempt_quality_rate") or 1.0)
        if task_class in weak_classes and (recurrence_pressure or benchmark_quality < 0.5):
            learning_adjust_grouped = 1 if complexity != "high" else 0
            learning_adjust_single = 2 if complexity != "high" else 1
            if benchmark_escalation >= 0.2:
                learning_adjust_single += 1
            learning_reason = "weak_class_recurrence_or_quality"

    effective_grouped = max(1, effective_grouped + learning_adjust_grouped)
    effective_single = max(1, effective_single + learning_adjust_single)
    return {
        "profile": selected_profile,
        "task_class": task_class,
        "complexity": complexity,
        "base_grouped_limit": base_grouped,
        "base_single_limit": base_single,
        "effective_grouped_limit": effective_grouped,
        "effective_single_limit": effective_single,
        "complexity_multiplier": multiplier,
        "learning_adjustment_applied": bool(learning_adjust_grouped or learning_adjust_single),
        "learning_adjustment_reason": learning_reason,
        "learning_adjustment_grouped": learning_adjust_grouped,
        "learning_adjustment_single": learning_adjust_single,
    }


def _load_recent_manager6_outcomes(*, days: int = DEFAULT_MANAGER6_HISTORY_WINDOW_DAYS) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc).timestamp() - (max(1, days) * 86400)
    outcomes: list[dict[str, Any]] = []
    plans_dir = TRACE_DIR / "plans"
    if not plans_dir.exists():
        return outcomes
    for path in plans_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        events = data.get("history", [])
        if not isinstance(events, list):
            continue
        for event in events:
            if event.get("event_type") != "attempt_finished":
                continue
            ts_raw = str(event.get("timestamp") or "")
            ts = None
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except ValueError:
                continue
            if ts < cutoff:
                continue
            for status in event.get("statuses", []) or []:
                if not isinstance(status, dict):
                    continue
                outcomes.append(status)
    return outcomes


def _strategy_scorecard(*, family: str, historical: list[dict[str, Any]]) -> dict[str, Any]:
    grouped_success = 0
    grouped_total = 0
    split_success = 0
    split_total = 0
    for row in historical:
        targets = [str(t) for t in row.get("targets", []) if t]
        row_family = ",".join(sorted({Path(t).stem.split("_")[0] for t in targets})) if targets else "unknown"
        if row_family != family:
            continue
        strategy = str(row.get("strategy") or "")
        retry_strategy = str(row.get("retry_strategy") or "")
        status = str(row.get("status") or "")
        ok = status in {"success", "partial_success", "dropped_preflight"}
        if retry_strategy == "split_on_failure" or strategy == "split_subplan":
            split_total += 1
            if ok:
                split_success += 1
            continue
        grouped_total += 1
        if ok:
            grouped_success += 1
    grouped_rate = (grouped_success / grouped_total) if grouped_total else 0.5
    split_rate = (split_success / split_total) if split_total else 0.5
    return {
        "family": family,
        "grouped_total": grouped_total,
        "grouped_success": grouped_success,
        "grouped_rate": round(grouped_rate, 3),
        "split_total": split_total,
        "split_success": split_success,
        "split_rate": round(split_rate, 3),
    }


def _choose_subplan_strategy(
    *,
    subplan: dict[str, Any],
    task_class: str,
    scorecard: dict[str, Any],
    family_memory: dict[str, Any],
    qualification_posture: dict[str, Any],
    budget_forecast: dict[str, Any],
    learning_priors: dict[str, Any],
    success_memory: dict[str, Any],
    resume_source_status: str | None,
) -> dict[str, Any]:
    risk_score = float(subplan.get("risk_score") or 0.0)
    yield_score = float(subplan.get("yield_score") or 0.0)
    size = int(subplan.get("size") or len(subplan.get("targets", [])) or 1)
    grouped_rate = float(scorecard.get("grouped_rate") or 0.5)
    split_rate = float(scorecard.get("split_rate") or 0.5)
    memory_escalation = float(family_memory.get("escalation_rate") or 0.0)
    memory_failure = float(family_memory.get("failure_rate") or 0.0)
    memory_samples = int(family_memory.get("samples") or 0)
    budget_remaining = int(budget_forecast.get("remaining") or 0)
    worker_pressure = bool(qualification_posture.get("worker_pressure"))
    qualification_caution = bool(qualification_posture.get("caution_mode"))
    learning_active = bool(learning_priors.get("active"))
    weak_classes = {str(item) for item in (learning_priors.get("weak_classes") or []) if item}
    recurrence_pressure = bool(learning_priors.get("recurrence_pressure"))
    benchmark_escalation = float(learning_priors.get("benchmark_escalation_rate") or 0.0)
    benchmark_quality = float(learning_priors.get("benchmark_first_attempt_quality_rate") or 1.0)
    success_preferred = str(success_memory.get("preferred_strategy") or "")
    success_confidence = float(success_memory.get("confidence") or 0.0)
    success_samples = int(success_memory.get("total_samples") or 0)
    resume_status = str(resume_source_status or "")

    strategy = "run_grouped"
    reason = "default_grouped"
    decision_tags: list[str] = []

    if resume_status in {"failure", "deferred_worker_budget", "dropped_family_budget"} and size > 1:
        strategy = "split_first"
        reason = "resume_failure_bias_split"
        decision_tags.append("resume_bias")
    elif (
        learning_active
        and task_class in weak_classes
        and size > 1
        and (
            recurrence_pressure
            or benchmark_escalation >= 0.22
            or benchmark_quality < 0.52
        )
    ):
        strategy = "split_first"
        reason = "learning_priors_bias_split"
        decision_tags.append("learning_priors")
    elif learning_active and task_class in weak_classes and size == 1 and benchmark_quality < 0.55:
        strategy = "run_grouped"
        reason = "learning_priors_single_target_guarded_grouped"
        decision_tags.append("learning_priors")
    elif worker_pressure and qualification_caution and budget_remaining <= 0 and yield_score < 12.0:
        decision_tags.append("qualification_budget_pressure")
        if size > 1:
            strategy = "split_first"
            reason = "qualification_worker_pressure_split_first"
        elif risk_score >= 2.0:
            strategy = "defer_manual"
            reason = "qualification_worker_pressure_high_risk_singleton_defer"
        else:
            strategy = "run_grouped"
            reason = "qualification_worker_pressure_low_risk_singleton_allow"
    elif size > 1 and (risk_score >= 1.8 or split_rate > grouped_rate + 0.12):
        strategy = "split_first"
        reason = "history_or_risk_prefers_split"
    elif size > 1 and memory_samples >= 5 and (memory_failure >= 0.35 or memory_escalation >= 0.35):
        strategy = "split_first"
        reason = "family_memory_prefers_split"
        decision_tags.append("family_memory")
    elif size == 1 and grouped_rate < 0.35 and yield_score < 6.0:
        strategy = "run_grouped"
        reason = "single_target_grouped_only"
    elif (
        size > 1
        and success_samples >= 3
        and success_confidence >= 0.65
        and success_preferred in {"split_first", "run_grouped"}
    ):
        strategy = success_preferred
        reason = f"manager15_success_memory_prefers_{success_preferred}"
        decision_tags.append("manager15_success_memory")

    return {
        "strategy": strategy,
        "reason": reason,
        "scorecard": scorecard,
        "family_memory": family_memory,
        "qualification_posture": qualification_posture,
        "budget_forecast": budget_forecast,
        "learning_priors": learning_priors,
        "success_memory": success_memory,
        "resume_source_status": resume_status or "",
        "decision_tags": decision_tags,
        "risk_score": round(risk_score, 3),
        "yield_score": round(yield_score, 3),
    }


def _load_learning_priors(*, path: Path, max_age_hours: int = 72) -> dict[str, Any]:
    if not path.exists():
        return {"active": False, "reason": "learning_priors_missing"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"active": False, "reason": "learning_priors_invalid_json"}

    generated_raw = str(payload.get("generated_at_utc") or "")
    generated_ts = None
    if generated_raw:
        try:
            generated_ts = datetime.fromisoformat(generated_raw.replace("Z", "+00:00"))
        except ValueError:
            generated_ts = None
    age_hours: float | None = None
    if generated_ts is not None:
        age_hours = max((datetime.now(timezone.utc) - generated_ts).total_seconds() / 3600.0, 0.0)
    fresh = age_hours is not None and age_hours <= max(1, max_age_hours)

    class_rows = payload.get("class_metrics")
    weak_classes: list[str] = []
    if isinstance(class_rows, list):
        for row in class_rows:
            if not isinstance(row, dict):
                continue
            class_id = str(row.get("class_id") or "")
            if not class_id:
                continue
            success_rate = float(row.get("success_rate") or 0.0)
            first_attempt = float(row.get("first_attempt_quality_rate") or 0.0)
            escalation_rate = float(row.get("escalation_rate") or 0.0)
            if success_rate < 0.7 or first_attempt < 0.5 or escalation_rate > 0.35:
                weak_classes.append(class_id)
    if not weak_classes:
        replay_queue = payload.get("replay_queue")
        if isinstance(replay_queue, list):
            weak_classes = sorted(
                {
                    str(item.get("task_class") or "")
                    for item in replay_queue
                    if isinstance(item, dict) and item.get("task_class")
                }
            )
        else:
            weak_classes = []

    metrics = payload.get("benchmark_metrics") if isinstance(payload.get("benchmark_metrics"), dict) else {}
    replay_queue = payload.get("replay_queue") if isinstance(payload.get("replay_queue"), list) else []
    bounded_replay_queue = [
        {
            "task_id": str(item.get("task_id") or ""),
            "task_class": str(item.get("task_class") or ""),
            "reason": str(item.get("reason") or ""),
            "source_plan_id": str(item.get("source_plan_id") or ""),
        }
        for item in replay_queue
        if isinstance(item, dict)
    ][:20]
    recurrence_rate = float(metrics.get("recurrence_rate") or 0.0)
    escalation_rate = float(metrics.get("escalation_rate") or 0.0)
    first_attempt_rate = float(metrics.get("first_attempt_quality_rate") or 0.0)

    active = bool(fresh and weak_classes)
    return {
        "active": active,
        "reason": "learning_priors_loaded" if active else ("learning_priors_stale_or_empty" if fresh else "learning_priors_stale"),
        "path": str(path),
        "generated_at_utc": generated_raw,
        "age_hours": round(age_hours, 3) if age_hours is not None else None,
        "fresh": fresh,
        "weak_classes": weak_classes,
        "recurrence_pressure": recurrence_rate > 0.35,
        "benchmark_recurrence_rate": recurrence_rate,
        "benchmark_escalation_rate": escalation_rate,
        "benchmark_first_attempt_quality_rate": first_attempt_rate,
        "replay_queue": bounded_replay_queue,
    }


def _load_latest_qualification_posture(*, max_age_hours: int = 48) -> dict[str, Any]:
    """Load bounded qualification posture for manager-side caution signals."""

    if not QUAL_HISTORY_PATH.exists():
        return {
            "source": "qualification_missing",
            "caution_mode": False,
            "worker_pressure": False,
            "age_hours": None,
        }

    last: dict[str, Any] | None = None
    with QUAL_HISTORY_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                last = row

    if not last:
        return {
            "source": "qualification_unreadable",
            "caution_mode": False,
            "worker_pressure": False,
            "age_hours": None,
        }

    ts_raw = str(last.get("timestamp") or "")
    age_hours: float | None = None
    if ts_raw:
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            age_hours = max((datetime.now(timezone.utc) - ts).total_seconds() / 3600.0, 0.0)
        except ValueError:
            age_hours = None

    fresh = age_hours is not None and age_hours <= max(1, max_age_hours)
    metrics = last.get("metrics") if isinstance(last.get("metrics"), dict) else {}
    stage8 = metrics.get("stage8") if isinstance(metrics.get("stage8"), dict) else {}
    worker = metrics.get("worker") if isinstance(metrics.get("worker"), dict) else {}
    gates = (
        last.get("v8_gate_assertions", {}).get("gates")
        if isinstance(last.get("v8_gate_assertions"), dict)
        else {}
    )
    if not isinstance(gates, dict):
        gates = {}

    worker_success = int(worker.get("success") or 0)
    worker_failure = int(worker.get("failure") or 0)
    worker_failure_rate = (worker_failure / (worker_success + worker_failure)) if (worker_success + worker_failure) else 0.0
    stage8_deferred = int(stage8.get("worker_budget_deferred_subplans") or 0)

    worker_pressure = bool(stage8_deferred > 0 or worker_failure_rate >= 0.22)
    caution_mode = bool(not gates.get("promotion8_ready", True) or worker_pressure)
    if not fresh:
        caution_mode = False

    return {
        "source": "qualification_history",
        "fresh": fresh,
        "age_hours": round(age_hours, 3) if age_hours is not None else None,
        "caution_mode": caution_mode,
        "worker_pressure": worker_pressure if fresh else False,
        "worker_failure_rate": round(worker_failure_rate, 3),
        "stage8_worker_budget_deferred_subplans": stage8_deferred,
        "promotion8_ready": bool(gates.get("promotion8_ready", False)),
        "qualification8_ready": bool(gates.get("qualification8_ready", False)),
    }


def build_promotion_env(lane: str, versions: dict[str, Any], manifest_version: int, manifest_path: Path) -> dict[str, str]:
    lane_cfg = versions.get("lane", {})
    env = {
        "PROMOTION_LANE": lane,
        "PROMOTION_LANE_STATUS": lane_cfg.get("status", ""),
        "PROMOTION_LANE_LABEL": lane_cfg.get("label", ""),
        "PROMOTION_STAGE_NAME": versions.get("stage", ""),
        "PROMOTION_STAGE_VERSION": versions.get("stage_version_name", ""),
        "PROMOTION_MANAGER_VERSION": versions.get("manager_version_name", ""),
        "PROMOTION_RAG_VERSION": versions.get("rag_version_name", ""),
        "PROMOTION_MANIFEST_VERSION": str(manifest_version),
        "PROMOTION_MANIFEST_PATH": str(manifest_path),
    }
    return env


def run_stage_rag6(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(STAGE_RAG6_PLAN),
        "--plan-id",
        args.plan_id,
        "--top",
        str(args.top),
        "--window",
        str(args.window),
        "--preview-lines",
        str(args.preview_lines),
        "--max-targets",
        str(args.rag_max_targets),
        "--max-subplans",
        str(args.max_subplans),
        "--subplan-size",
        str(args.subplan_size),
        "--related-limit",
        str(args.related_limit),
        "--history-window",
        str(args.history_window),
    ]
    if args.notes:
        cmd.extend(["--notes", args.notes])
    for prefix in args.preferred_prefix:
        cmd.extend(["--preferred-prefix", prefix])
    cmd.extend(args.query)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def _write_stage6_jobs_file(jobs: list[dict[str, Any]]) -> Path:
    payload = list(jobs)
    file_path = Path(tempfile.mkstemp(prefix="stage7-subplan-", suffix=".json")[1])
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def _load_stage6_attempt_code_outcomes(stage6_plan_id: str) -> dict[str, Any]:
    stage6_history_path = TRACE_DIR / "plans" / f"{stage6_plan_id}.json"
    if not stage6_history_path.exists():
        return {"available": False, "reason": "stage6_history_missing"}
    try:
        history_payload = json.loads(stage6_history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"available": False, "reason": "stage6_history_invalid_json"}
    history = history_payload.get("history")
    if not isinstance(history, list):
        return {"available": False, "reason": "stage6_history_missing_events"}
    finished: dict[str, Any] | None = None
    for event in reversed(history):
        if str(event.get("event_type") or "") == "attempt_finished":
            finished = event if isinstance(event, dict) else None
            break
    if not finished:
        return {"available": False, "reason": "stage6_attempt_finished_missing"}
    statuses = [row for row in (finished.get("statuses") or []) if isinstance(row, dict)]
    if not statuses:
        return {"available": False, "reason": "stage6_statuses_empty"}

    checks: dict[str, dict[str, int]] = {}
    diff_total = 0
    diff_passed = 0
    rows_with_code = 0

    def _add_check(name: str, total: int, passed: int) -> None:
        bucket = checks.setdefault(name, {"total": 0, "passed": 0})
        bucket["total"] += max(0, total)
        bucket["passed"] += max(0, min(passed, total if total > 0 else passed))

    for row in statuses:
        code_outcomes = row.get("code_outcomes")
        if not isinstance(code_outcomes, dict):
            continue
        rows_with_code += 1
        for key, block in code_outcomes.items():
            if key in {"summary", "per_file", "committed_files", "expected_files"}:
                continue
            if not isinstance(block, dict):
                continue
            if "total" not in block or "passed" not in block:
                continue
            total = int(block.get("total") or 0)
            passed = int(block.get("passed") or 0)
            _add_check(key, total, passed)
        summary = code_outcomes.get("summary")
        if isinstance(summary, dict) and "diff_integrity_ok" in summary:
            diff_total += 1
            if bool(summary.get("diff_integrity_ok")):
                diff_passed += 1

    total_checks = sum(v["total"] for v in checks.values())
    passed_checks = sum(v["passed"] for v in checks.values())
    check_rate = round((passed_checks / total_checks), 3) if total_checks > 0 else 0.0
    diff_rate = round((diff_passed / diff_total), 3) if diff_total > 0 else 0.0
    coverage = round((rows_with_code / len(statuses)), 3) if statuses else 0.0
    return {
        "available": rows_with_code > 0,
        "status_count": len(statuses),
        "code_status_count": rows_with_code,
        "code_coverage_rate": coverage,
        "check_rate": check_rate,
        "checks_total": total_checks,
        "checks_passed": passed_checks,
        "diff_integrity_rate": diff_rate,
        "checks": checks,
        "python_compile": checks.get("python_compile", {"total": 0, "passed": 0}),
        "shell_syntax": checks.get("shell_syntax", {"total": 0, "passed": 0}),
    }


def _single_line_import_base(value: str) -> str | None:
    if "\n" in value:
        return None
    text = value.strip()
    if not text:
        return None
    comment_idx = text.find("#")
    if comment_idx != -1:
        text = text[:comment_idx].rstrip()
    if IMPORT_BASE_RE.match(text):
        return text
    return None


def _target_supports_literal_contract(path: str, literal_old: str, literal_new: str) -> tuple[bool, str]:
    target_path = (REPO_ROOT / path).resolve()
    try:
        contents = target_path.read_text(encoding="utf-8")
    except OSError:
        return False, "unreadable_target"

    if literal_old in contents or literal_new in contents:
        return True, "literal_present"

    base_old = _single_line_import_base(literal_old)
    base_new = _single_line_import_base(literal_new)
    if base_old and base_new and base_old == base_new:
        for line in contents.splitlines():
            if line.strip().startswith(base_old):
                return True, "import_base_match"
    return False, "literal_mismatch_preflight"


def _derive_target_contract(path: str, literal_old: str, literal_new: str) -> dict[str, Any]:
    target_path = (REPO_ROOT / path).resolve()
    try:
        contents = target_path.read_text(encoding="utf-8")
    except OSError:
        return {
            "supported": False,
            "reason": "unreadable_target",
            "path": path,
        }

    supported, reason = _target_supports_literal_contract(path, literal_old, literal_new)
    if supported:
        return {
            "supported": True,
            "reason": reason,
            "path": path,
            "contract_strategy": "global_literal_contract",
            "literal_old": literal_old,
            "literal_new": literal_new,
        }

    is_shell_like = path.endswith(".sh")
    if not is_shell_like:
        first_line = contents.splitlines()[0].strip() if contents.splitlines() else ""
        if first_line.startswith("#!") and ("sh" in first_line or "bash" in first_line):
            is_shell_like = True
    if is_shell_like:
        def _safe_shell_literal_line(text: str) -> bool:
            stripped = text.strip()
            if not stripped:
                return False
            if stripped.startswith("#!"):
                return False
            if SHELL_RISKY_TOKEN_RE.search(stripped):
                return False
            return True

        for line in contents.splitlines():
            text = line.rstrip()
            if not text or text.lstrip().startswith("#"):
                continue
            if SHELL_STRICT_RE.match(text):
                continue
            if SHELL_ASSIGNMENT_RE.match(text) and _safe_shell_literal_line(text):
                return {
                    "supported": True,
                    "reason": "derived_shell_assignment_line",
                    "path": path,
                    "contract_strategy": "shell_assignment_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  # stage7-op",
                }
        for line in contents.splitlines():
            text = line.rstrip()
            if not text or text.lstrip().startswith("#"):
                continue
            if SHELL_PRINT_RE.match(text) and _safe_shell_literal_line(text):
                return {
                    "supported": True,
                    "reason": "derived_shell_print_line",
                    "path": path,
                    "contract_strategy": "shell_print_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  # stage7-op",
                }
        for line in contents.splitlines():
            text = line.rstrip()
            stripped = text.strip()
            if not stripped or stripped.startswith("#!"):
                continue
            if stripped.startswith("#") and _safe_shell_literal_line(text):
                return {
                    "supported": True,
                    "reason": "derived_shell_comment_line",
                    "path": path,
                    "contract_strategy": "shell_comment_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  [stage7-op]",
                }
        for line in contents.splitlines():
            if SHELL_STRICT_RE.match(line):
                base_old = line.rstrip()
                return {
                    "supported": True,
                    "reason": "derived_shell_strict_mode_line",
                    "path": path,
                    "contract_strategy": "shell_strict_mode_literal",
                    "literal_old": base_old,
                    "literal_new": f"{base_old}  # stage7-op",
                }
        return {
            "supported": False,
            "reason": "no_safe_anchor_script",
            "path": path,
            "contract_strategy": "shell_no_safe_anchor",
        }

    if path.endswith(".py"):
        for line in contents.splitlines():
            text = line.rstrip()
            if IMPORT_BASE_RE.match(text.strip()):
                return {
                    "supported": True,
                    "reason": "derived_python_import_line",
                    "path": path,
                    "contract_strategy": "python_import_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  # stage7-op",
                }

    return {
        "supported": False,
        "reason": "literal_mismatch_preflight",
        "path": path,
    }


def run_stage6_subplan(
    *,
    subplan: dict[str, Any],
    args: argparse.Namespace,
    env: dict[str, str],
    op_index: int,
    strategy_tag: str = "grouped_subplan",
    strategy_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    subplan_id = str(subplan.get("subplan_id") or f"subplan-{op_index + 1}")
    requested_targets = [str(t) for t in subplan.get("targets", []) if t]
    accepted_jobs: list[dict[str, Any]] = []
    accepted_targets: list[str] = []
    accepted_contracts: list[dict[str, Any]] = []
    dropped_targets: list[dict[str, str]] = []
    for target in requested_targets:
        contract = _derive_target_contract(target, args.literal_old, args.literal_new)
        if contract.get("supported"):
            accepted_targets.append(target)
            accepted_contracts.append(
                {
                    "path": target,
                    "contract_strategy": contract.get("contract_strategy", "global_literal_contract"),
                    "reason": contract.get("reason"),
                }
            )
            accepted_jobs.append(
                {
                    "path": target,
                    "source": "stage7-subplan",
                    "literal_old": contract.get("literal_old", args.literal_old),
                    "literal_new": contract.get("literal_new", args.literal_new),
                    "sync_reason": contract.get("reason"),
                }
            )
        else:
            dropped_targets.append({"path": target, "reason": str(contract.get("reason") or "literal_mismatch_preflight")})

    if not accepted_targets:
        rollback_contract = {
            "contract_version": "stage9-v1",
            "strategy": "preflight_drop_no_dispatch",
            "rollback_scope": [],
            "trigger_on_failure": False,
            "verification": "not_applicable_no_dispatch",
            "notes": "No stage6/stage5 dispatch occurred; no rollback action required.",
        }
        status = {
            "subplan_id": subplan_id,
            "targets": [],
            "target_contracts": [],
            "dropped_targets": dropped_targets,
            "status": "dropped_preflight",
            "return_code": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "strategy": strategy_tag,
            "strategy_decision": strategy_decision or {},
            "rollback_contract": rollback_contract,
            "code_outcomes": {"available": False, "reason": "no_dispatch_preflight_drop"},
        }
        return status

    targets = accepted_targets
    jobs_file = _write_stage6_jobs_file(accepted_jobs)
    started = datetime.now(timezone.utc).isoformat()

    cmd = [
        sys.executable,
        str(STAGE6_MANAGER),
        "--query",
        *args.query,
        "--plan-id",
        f"{args.plan_id}-{subplan_id}",
        "--commit-msg",
        f"{args.commit_msg} - {subplan_id}",
        "--jobs-file",
        str(jobs_file),
        "--max-entries",
        str(args.max_entries_per_subplan),
        "--retry-class",
        args.retry_class,
        "--group-failure-policy",
        args.group_failure_policy,
        "--max-secondary-retries",
        str(args.max_secondary_retries),
        "--max-secondary-rescues",
        str(args.max_secondary_rescues),
        "--plan-status",
        args.plan_status,
        "--related-limit",
        str(args.related_limit),
        "--history-window",
        str(args.history_window),
        "--literal-old",
        args.literal_old,
        "--literal-new",
        args.literal_new,
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    proc = subprocess.run(cmd, env={**os.environ, **env})
    jobs_file.unlink(missing_ok=True)
    stage6_plan_id = f"{args.plan_id}-{subplan_id}"
    code_outcomes = _load_stage6_attempt_code_outcomes(stage6_plan_id)
    rollback_contract = {
        "contract_version": "stage9-v1",
        "strategy": "delegated_stage6_stage5_bounded_commit",
        "rollback_scope": targets,
        "trigger_on_failure": proc.returncode != 0,
        "verification": "stage6_return_code",
        "notes": "Rollback boundary remains delegated to stage6/stage5 guards; no global repo reset.",
    }
    status = {
        "subplan_id": subplan_id,
        "targets": targets,
        "target_contracts": accepted_contracts,
        "dropped_targets": dropped_targets,
        "status": "success" if proc.returncode == 0 else "failure",
        "return_code": proc.returncode,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy_tag,
        "strategy_decision": strategy_decision or {},
        "rollback_contract": rollback_contract,
        "stage6_plan_id": stage6_plan_id,
        "code_outcomes": code_outcomes,
    }
    return status


def _run_split_recovery(
    *,
    failed_subplan: dict[str, Any],
    args: argparse.Namespace,
    env: dict[str, str],
    statuses: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    split_statuses: list[dict[str, Any]] = []
    all_success = True
    for idx, path in enumerate(failed_subplan.get("targets", [])):
        single = {
            "subplan_id": f"{failed_subplan.get('subplan_id')}-split-{idx + 1}",
            "targets": [path],
        }
        status = run_stage6_subplan(subplan=single, args=args, env=env, op_index=len(statuses) + len(split_statuses))
        status["strategy"] = "split_subplan"
        status["retry"] = True
        status["retry_strategy"] = "split_on_failure"
        status["refinement_of_subplan"] = failed_subplan.get("subplan_id")
        split_statuses.append(status)
        if status["return_code"] != 0:
            all_success = False
    return all_success, split_statuses


def _risk_rank(bucket: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(bucket, 2)


def _order_subplans(subplans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Risk/conflict-aware ordering for Stage-7 subplan execution.

    Lower-risk, non-overlapping families run first to reduce early brittle failures.
    """
    pending = [dict(item) for item in subplans]
    ordered: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    while pending:
        best_idx = 0
        best_key: tuple[int, int, float] | None = None
        for idx, subplan in enumerate(pending):
            meta = subplan.get("target_meta") or []
            families = {str(m.get("family") or "") for m in meta if m.get("family")}
            conflict_count = len(families & seen_families)
            worst_risk = max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in meta), default=2)
            confidence = float(subplan.get("confidence") or 0.0)
            yield_score = float(subplan.get("yield_score") or 0.0)
            key = (conflict_count, worst_risk, -yield_score, -confidence)
            if best_key is None or key < best_key:
                best_key = key
                best_idx = idx
        chosen = pending.pop(best_idx)
        meta = chosen.get("target_meta") or []
        families = sorted({str(m.get("family") or "") for m in meta if m.get("family")})
        chosen["execution_ordering"] = {
            "risk_rank": max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in meta), default=2),
            "family_conflicts_with_prior": len(set(families) & seen_families),
            "families": families,
            "yield_score": round(float(chosen.get("yield_score") or 0.0), 3),
            "reason": "risk_conflict_yield_aware_order",
        }
        seen_families.update(families)
        ordered.append(chosen)
    return ordered


def _subplan_families(subplan: dict[str, Any]) -> set[str]:
    meta = subplan.get("target_meta") or []
    families = {str(m.get("family") or "") for m in meta if m.get("family")}
    if families:
        return {f for f in families if f}
    targets = [str(t) for t in (subplan.get("targets") or []) if t]
    return {Path(t).stem.split("_")[0] for t in targets if t}


def _build_hierarchical_decomposition(
    subplans: list[dict[str, Any]],
    *,
    recurrence_memory: dict[str, Any],
) -> dict[str, Any]:
    """Manager-11 hierarchical decomposition for mixed-family cohort construction.

    This is a bounded two-level hierarchy:
    - parent cohorts (priority groups)
    - child subplans within each cohort
    """

    pending = [dict(item) for item in subplans]
    cohorts: list[dict[str, Any]] = []
    ordered: list[dict[str, Any]] = []
    contexts: dict[str, dict[str, Any]] = {}
    cohort_idx = 1

    def _seed_key(item: dict[str, Any]) -> tuple[float, float, float]:
        return (
            float(item.get("yield_score") or 0.0),
            float(item.get("confidence") or 0.0),
            -float(item.get("risk_score") or 0.0),
        )

    conservative_split = bool(recurrence_memory.get("conservative_split"))
    while pending:
        pending.sort(key=_seed_key, reverse=True)
        seed = pending.pop(0)
        members = [seed]
        seed_families = set(_subplan_families(seed))
        cohort_families = set(seed_families)

        best_idx: int | None = None
        best_score = -999.0
        for idx, cand in enumerate(pending):
            cand_families = set(_subplan_families(cand))
            if not cand_families:
                continue
            overlap = len(cohort_families & cand_families)
            if overlap >= len(cand_families):
                continue
            risk_penalty = float(cand.get("risk_score") or 0.0) * 0.6
            yield_bonus = float(cand.get("yield_score") or 0.0) * 0.25
            novelty = float(len(cand_families - cohort_families)) * 1.8
            score = novelty + yield_bonus - risk_penalty - (overlap * 1.5)
            if score > best_score:
                best_score = score
                best_idx = idx

        # Keep the hierarchy bounded: at most 2 child subplans per cohort.
        if best_idx is not None and best_score >= (2.5 if conservative_split else 0.5):
            child = pending.pop(best_idx)
            child_families = _subplan_families(child)
            if conservative_split and len((cohort_families | child_families)) > 1:
                pending.append(child)
            else:
                members.append(child)
                cohort_families |= child_families

        cohort_id = f"cohort-{cohort_idx}"
        cohort_idx += 1
        mixed_family = len(cohort_families) > 1
        ordered_members = sorted(
            members,
            key=lambda item: (
                float(item.get("risk_score") or 0.0),
                -float(item.get("yield_score") or 0.0),
                -float(item.get("confidence") or 0.0),
            ),
        )
        for member_idx, item in enumerate(ordered_members, start=1):
            subplan_id = str(item.get("subplan_id") or "")
            role = "parent_head" if member_idx == 1 else "child_member"
            item["hierarchy_context"] = {
                "manager_version": "manager15-v1",
                "cohort_id": cohort_id,
                "cohort_role": role,
                "cohort_size": len(ordered_members),
                "cohort_families": sorted(cohort_families),
                "mixed_family_cohort": mixed_family,
                "decomposition_depth": 2,
            }
            if subplan_id:
                contexts[subplan_id] = dict(item["hierarchy_context"])
            ordered.append(item)
        cohorts.append(
            {
                "cohort_id": cohort_id,
                "strategy": (
                    "recurrence_split_cohort"
                    if conservative_split
                    else ("mixed_family_hierarchical_cohort" if mixed_family else "single_family_hierarchical_cohort")
                ),
                "subplan_ids": [str(item.get("subplan_id") or "") for item in ordered_members],
                "families": sorted(cohort_families),
                "mixed_family": mixed_family,
                "cohort_priority": len(cohorts) + 1,
            }
        )

    mixed_count = sum(1 for c in cohorts if bool(c.get("mixed_family")))
    return {
        "ordered_subplans": ordered,
        "cohorts": cohorts,
        "contexts": contexts,
        "summary": {
            "cohort_count": len(cohorts),
            "mixed_family_cohort_count": mixed_count,
            "single_family_cohort_count": len(cohorts) - mixed_count,
            "decomposition_mode": str(recurrence_memory.get("decomposition_mode") or "balanced_hierarchical"),
        },
    }


def _load_cross_run_recurrence_memory(
    *,
    task_class: str,
    history_window_days: int,
    learning_priors: dict[str, Any],
) -> dict[str, Any]:
    """Manager-12 recurrence/cohort memory from replay queue + recent outcomes."""

    replay_queue = learning_priors.get("replay_queue")
    if not isinstance(replay_queue, list):
        replay_queue = []
    replay_rows = [
        row
        for row in replay_queue
        if isinstance(row, dict) and str(row.get("task_class") or "") == task_class
    ]
    replay_reasons = sorted({str(row.get("reason") or "") for row in replay_rows if row.get("reason")})
    replay_pressure = bool(replay_rows)

    recent_runs = 0
    bad_runs = 0
    strategy_totals: dict[str, int] = {}
    strategy_bad: dict[str, int] = {}
    family_totals: dict[str, int] = {}
    family_bad: dict[str, int] = {}
    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff_ts = now_ts - (max(1, history_window_days) * 86400)
    plans_dir = TRACE_DIR / "plans"
    if plans_dir.exists():
        for path in plans_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            plan_payload = data.get("plan_payload") if isinstance(data.get("plan_payload"), dict) else {}
            row_task_class = _infer_task_class_from_query(str(plan_payload.get("query") or ""))
            if row_task_class != task_class:
                continue
            finished = None
            history = data.get("history") if isinstance(data.get("history"), list) else []
            for event in reversed(history):
                if isinstance(event, dict) and str(event.get("event_type") or "") == "attempt_finished":
                    finished = event
                    break
            if not isinstance(finished, dict):
                continue
            try:
                ts = datetime.fromisoformat(str(finished.get("timestamp") or "").replace("Z", "+00:00")).timestamp()
            except ValueError:
                continue
            if ts < cutoff_ts:
                continue
            recent_runs += 1
            statuses = finished.get("statuses") if isinstance(finished.get("statuses"), list) else []
            run_bad = False
            for row in statuses:
                if not isinstance(row, dict):
                    continue
                status = str(row.get("status") or "")
                strategy = str(row.get("strategy") or "unknown")
                strategy_decision = row.get("strategy_decision") if isinstance(row.get("strategy_decision"), dict) else {}
                family = str(strategy_decision.get("family") or "unknown")
                strategy_totals[strategy] = strategy_totals.get(strategy, 0) + 1
                family_totals[family] = family_totals.get(family, 0) + 1
                is_bad = status in {
                    "failure",
                    "deferred_worker_budget",
                    "deferred_manager_policy",
                    "dropped_family_budget",
                    "rollback_contract_invalid",
                }
                if is_bad:
                    run_bad = True
                    strategy_bad[strategy] = strategy_bad.get(strategy, 0) + 1
                    family_bad[family] = family_bad.get(family, 0) + 1
            if run_bad:
                bad_runs += 1

    bad_rate = round((bad_runs / recent_runs), 3) if recent_runs > 0 else 0.0
    strategy_bad_rates = {
        key: round((strategy_bad.get(key, 0) / total), 3) if total > 0 else 0.0
        for key, total in strategy_totals.items()
    }
    family_bad_rates = {
        key: round((family_bad.get(key, 0) / total), 3) if total > 0 else 0.0
        for key, total in family_totals.items()
    }
    conservative_split = bool(replay_pressure or bad_rate >= 0.35)
    return {
        "task_class": task_class,
        "replay_pressure": replay_pressure,
        "replay_count": len(replay_rows),
        "replay_reasons": replay_reasons,
        "recent_runs": recent_runs,
        "recent_bad_runs": bad_runs,
        "recent_bad_rate": bad_rate,
        "strategy_bad_rates": strategy_bad_rates,
        "family_bad_rates": family_bad_rates,
        "conservative_split": conservative_split,
        "decomposition_mode": "recurrence_aware_conservative_split" if conservative_split else "balanced_hierarchical",
    }


def _load_cross_run_success_memory(
    *,
    task_class: str,
    history_window_days: int,
) -> dict[str, Any]:
    """Manager-15 success-memory signals for proactive first-attempt strategy biasing."""

    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff_ts = now_ts - (max(1, history_window_days) * 86400)
    family_stats: dict[str, dict[str, int]] = {}
    plans_dir = TRACE_DIR / "plans"
    if not plans_dir.exists():
        return {"task_class": task_class, "families": {}, "history_rows": 0}

    history_rows = 0
    for path in plans_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        plan_payload = data.get("plan_payload") if isinstance(data.get("plan_payload"), dict) else {}
        row_task_class = _infer_task_class_from_query(str(plan_payload.get("query") or ""))
        if row_task_class != task_class:
            continue
        finished = None
        history = data.get("history") if isinstance(data.get("history"), list) else []
        for event in reversed(history):
            if isinstance(event, dict) and str(event.get("event_type") or "") == "attempt_finished":
                finished = event
                break
        if not isinstance(finished, dict):
            continue
        try:
            ts = datetime.fromisoformat(str(finished.get("timestamp") or "").replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if ts < cutoff_ts:
            continue

        statuses = finished.get("statuses") if isinstance(finished.get("statuses"), list) else []
        for row in statuses:
            if not isinstance(row, dict):
                continue
            subplan_id = str(row.get("subplan_id") or "")
            if "-split-" in subplan_id or "-manager14-" in subplan_id:
                continue
            strategy_decision = row.get("strategy_decision") if isinstance(row.get("strategy_decision"), dict) else {}
            strategy = str(strategy_decision.get("strategy") or "")
            if strategy not in {"run_grouped", "split_first"}:
                continue
            family = str(strategy_decision.get("family") or _subplan_family_key(row) or "unknown")
            if not family:
                family = "unknown"
            status = str(row.get("status") or "")
            ok = status in {"success", "partial_success", "dropped_preflight", "resumed_skip_completed"}
            bucket = family_stats.setdefault(
                family,
                {
                    "run_grouped_total": 0,
                    "run_grouped_success": 0,
                    "split_first_total": 0,
                    "split_first_success": 0,
                },
            )
            key_total = f"{strategy}_total"
            key_success = f"{strategy}_success"
            bucket[key_total] += 1
            if ok:
                bucket[key_success] += 1
            history_rows += 1

    families: dict[str, dict[str, Any]] = {}
    for family, row in family_stats.items():
        grouped_total = int(row.get("run_grouped_total") or 0)
        grouped_success = int(row.get("run_grouped_success") or 0)
        split_total = int(row.get("split_first_total") or 0)
        split_success = int(row.get("split_first_success") or 0)
        grouped_rate = (grouped_success / grouped_total) if grouped_total else 0.0
        split_rate = (split_success / split_total) if split_total else 0.0
        total_samples = grouped_total + split_total
        preferred_strategy = ""
        confidence = 0.0
        if total_samples >= 3:
            if split_rate >= grouped_rate + 0.12 and split_total >= 2:
                preferred_strategy = "split_first"
                confidence = split_rate
            elif grouped_rate >= split_rate + 0.12 and grouped_total >= 2:
                preferred_strategy = "run_grouped"
                confidence = grouped_rate
        families[family] = {
            "preferred_strategy": preferred_strategy,
            "confidence": round(confidence, 3),
            "grouped_rate": round(grouped_rate, 3),
            "split_rate": round(split_rate, 3),
            "grouped_samples": grouped_total,
            "split_samples": split_total,
            "total_samples": total_samples,
        }
    return {
        "task_class": task_class,
        "history_rows": history_rows,
        "families": families,
    }


def _apply_manager13_predispatch_shaping(
    *,
    subplans: list[dict[str, Any]],
    strategy_decisions: dict[str, dict[str, Any]],
    recurrence_memory: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Manager-13 pre-dispatch shaping using cross-run recurrence trends."""

    family_bad_rates = recurrence_memory.get("family_bad_rates")
    if not isinstance(family_bad_rates, dict):
        family_bad_rates = {}
    strategy_bad_rates = recurrence_memory.get("strategy_bad_rates")
    if not isinstance(strategy_bad_rates, dict):
        strategy_bad_rates = {}
    replay_pressure = bool(recurrence_memory.get("replay_pressure"))
    recent_bad_rate = float(recurrence_memory.get("recent_bad_rate") or 0.0)
    grouped_bad_rate = float(strategy_bad_rates.get("grouped_subplan") or 0.0)

    shaped_subplans: list[dict[str, Any]] = []
    split_first_count = 0
    proactive_defer_count = 0
    predispatch_drop_count = 0

    for original in subplans:
        subplan = dict(original)
        subplan_id = str(subplan.get("subplan_id") or "")
        decision = strategy_decisions.setdefault(
            subplan_id,
            {"strategy": "run_grouped", "reason": "manager13_default_grouped"},
        )
        family = str(decision.get("family") or _subplan_family_key(subplan) or "unknown")
        family_bad_rate = float(family_bad_rates.get(family) or 0.0)
        targets = [str(t) for t in (subplan.get("targets") or []) if t]
        target_meta = subplan.get("target_meta") if isinstance(subplan.get("target_meta"), list) else []
        risk_rank = max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in target_meta), default=2)
        shape_tags = list(decision.get("decision_tags") or [])

        if replay_pressure and len(targets) > 1 and (family_bad_rate >= 0.35 or grouped_bad_rate >= 0.45):
            if decision.get("strategy") not in {"defer_manual"}:
                decision["strategy"] = "split_first"
                decision["reason"] = "manager13_proactive_split_from_recurrence"
                split_first_count += 1
                shape_tags.append("manager13_proactive_split")

        if replay_pressure and len(targets) > 1 and family_bad_rate >= 0.65 and risk_rank >= 1:
            drop_count = len(targets) - 1
            if drop_count > 0:
                dropped = [{"path": path, "reason": "manager13_predispatch_drop_high_recurrence"} for path in targets[1:]]
                subplan["targets"] = targets[:1]
                existing = subplan.get("predispatch_dropped_targets")
                if isinstance(existing, list):
                    subplan["predispatch_dropped_targets"] = existing + dropped
                else:
                    subplan["predispatch_dropped_targets"] = dropped
                predispatch_drop_count += drop_count
                shape_tags.append("manager13_predispatch_drop")

        if (
            replay_pressure
            and recent_bad_rate >= 0.5
            and len(targets) == 1
            and family_bad_rate >= 0.8
            and risk_rank >= 2
            and decision.get("strategy") not in {"defer_manual"}
        ):
            decision["strategy"] = "defer_manual"
            decision["reason"] = "manager13_proactive_defer_high_recurrence"
            proactive_defer_count += 1
            shape_tags.append("manager13_proactive_defer")

        decision["predispatch_shape"] = {
            "family_bad_rate": round(family_bad_rate, 3),
            "grouped_bad_rate": round(grouped_bad_rate, 3),
            "risk_rank": int(risk_rank),
            "replay_pressure": replay_pressure,
        }
        decision["decision_tags"] = sorted(set(shape_tags))
        strategy_decisions[subplan_id] = decision
        shaped_subplans.append(subplan)

    def _order_key(item: dict[str, Any]) -> tuple[float, int, float]:
        subplan_id = str(item.get("subplan_id") or "")
        decision = strategy_decisions.get(subplan_id, {})
        family = str(decision.get("family") or _subplan_family_key(item) or "unknown")
        family_bad_rate = float(family_bad_rates.get(family) or 0.0)
        target_meta = item.get("target_meta") if isinstance(item.get("target_meta"), list) else []
        risk_rank = max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in target_meta), default=2)
        yield_score = float(item.get("yield_score") or 0.0)
        return (family_bad_rate, risk_rank, -yield_score)

    ordered = sorted(shaped_subplans, key=_order_key)
    for idx, item in enumerate(ordered, start=1):
        subplan_id = str(item.get("subplan_id") or "")
        strategy_decisions.setdefault(subplan_id, {})["predispatch_priority"] = idx

    return ordered, {
        "enabled": bool(replay_pressure or recent_bad_rate >= 0.35),
        "strategy": "manager13_proactive_predispatch_shaping",
        "split_first_count": split_first_count,
        "proactive_defer_count": proactive_defer_count,
        "predispatch_drop_count": predispatch_drop_count,
        "ordered_subplan_ids": [str(item.get("subplan_id") or "") for item in ordered],
        "recent_bad_rate": round(recent_bad_rate, 3),
        "grouped_bad_rate": round(grouped_bad_rate, 3),
    }


def _apply_manager14_budget_fallback_shaping(
    *,
    subplans: list[dict[str, Any]],
    strategy_decisions: dict[str, dict[str, Any]],
    recurrence_memory: dict[str, Any],
) -> dict[str, Any]:
    """Manager-14 proactive budget fallback shaping.

    When grouped-budget pressure is likely to defer a whole grouped subplan, enable
    bounded singleton fallback so at least part of the work can continue locally.
    """

    strategy_bad_rates = recurrence_memory.get("strategy_bad_rates")
    if not isinstance(strategy_bad_rates, dict):
        strategy_bad_rates = {}
    replay_pressure = bool(recurrence_memory.get("replay_pressure"))
    recent_bad_rate = float(recurrence_memory.get("recent_bad_rate") or 0.0)
    grouped_bad_rate = float(strategy_bad_rates.get("grouped_subplan") or 0.0)

    enabled = bool(replay_pressure or recent_bad_rate >= 0.35 or grouped_bad_rate >= 0.35)
    grouped_candidate_count = 0
    singleton_candidate_count = 0
    enabled_count = 0
    for subplan in subplans:
        targets = [str(t) for t in (subplan.get("targets") or []) if t]
        if not targets:
            continue
        if len(targets) > 1:
            grouped_candidate_count += 1
        else:
            singleton_candidate_count += 1
        subplan_id = str(subplan.get("subplan_id") or "")
        decision = strategy_decisions.setdefault(subplan_id, {})
        decision["manager14_budget_fallback_enabled"] = bool(enabled)
        decision["manager14_budget_fallback_reason"] = (
            "manager14_replay_or_grouped_budget_recurrence_pressure" if enabled else "manager14_fallback_not_needed"
        )
        tags = list(decision.get("decision_tags") or [])
        if enabled:
            tags.append("manager14_budget_fallback_ready")
            enabled_count += 1
        decision["decision_tags"] = sorted(set(tags))
        strategy_decisions[subplan_id] = decision

    return {
        "enabled": enabled,
        "strategy": "manager14_budget_constrained_singleton_fallback",
        "candidate_grouped_subplans": grouped_candidate_count,
        "candidate_singleton_subplans": singleton_candidate_count,
        "fallback_enabled_subplans": enabled_count,
        "recent_bad_rate": round(recent_bad_rate, 3),
        "grouped_bad_rate": round(grouped_bad_rate, 3),
        "replay_pressure": replay_pressure,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage-7 multi-plan manager")
    parser.add_argument("--query", nargs="+", required=True)
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--commit-msg", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--plan-status", default="preview")

    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--window", type=int, default=25)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--rag-max-targets", type=int, default=9)
    parser.add_argument("--max-subplans", type=int, default=3)
    parser.add_argument("--subplan-size", type=int, default=3)
    parser.add_argument("--max-entries-per-subplan", type=int, default=3)
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument("--history-window", type=int, default=15)

    parser.add_argument(
        "--retry-class",
        choices=["none", "fallback_on_empty", "fallback_on_failure", "adaptive_group_retry"],
        default="adaptive_group_retry",
    )
    parser.add_argument(
        "--group-failure-policy",
        choices=["abort", "continue_on_secondary_failure"],
        default="continue_on_secondary_failure",
    )
    parser.add_argument("--max-secondary-retries", type=int, default=1)
    parser.add_argument("--max-secondary-rescues", type=int, default=1)
    parser.add_argument("--literal-old", default="import argparse", help="Literal old text for delegated Stage-6 jobs")
    parser.add_argument(
        "--literal-new",
        default="import argparse  # stage7-op",
        help="Literal new text for delegated Stage-6 jobs",
    )

    parser.add_argument(
        "--subplan-failure-policy",
        choices=["abort", "split_on_failure", "continue"],
        default="split_on_failure",
        help="Manager-6 policy when a grouped Stage-7 subplan fails.",
    )
    parser.add_argument(
        "--preferred-prefix",
        action="append",
        default=[],
        help="Preferred retrieval prefix for Stage RAG-6 ranking (repeatable).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manager-history-window-days", type=int, default=14)
    parser.add_argument("--manager-memory-window-days", type=int, default=30)
    parser.add_argument("--qualification-max-age-hours", type=int, default=48)
    parser.add_argument("--family-rescue-budget", type=int, default=1)
    parser.add_argument("--worker-budget-grouped", type=int, default=4)
    parser.add_argument("--worker-budget-single", type=int, default=8)
    parser.add_argument("--worker-budget-adaptive-window-days", type=int, default=14)
    parser.add_argument(
        "--learning-priors-path",
        default=str(LEARNING_LATEST_PATH),
        help="Learning-loop priors artifact used by Manager-10 policy adaptation.",
    )
    parser.add_argument(
        "--learning-priors-max-age-hours",
        type=int,
        default=72,
        help="Maximum artifact age for learning priors before ignored as stale.",
    )
    parser.add_argument(
        "--disable-learning-priors",
        action="store_true",
        help="Disable learning-prior strategy adaptation and use baseline manager policy.",
    )
    parser.add_argument(
        "--worker-budget-profile",
        default="auto",
        help="Worker budget profile from manifest worker_budget_profiles (or auto).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an existing Stage-7 plan from persisted checkpoints and skip completed subplans.",
    )
    parser.add_argument(
        "--stop-after-subplans",
        type=int,
        default=0,
        help="Bounded test control: stop cleanly after N subplans and persist checkpoints.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest_cfg = load_manifest(manifest_path)
    lane_name = "stage7"
    versions = resolve_versions_for_lane(manifest_cfg.data, lane_name)
    if not args.preferred_prefix:
        lane_cfg = versions.get("lane", {})
        args.preferred_prefix = list(lane_cfg.get("allowed_targets", ["bin/"]))

    checkpoint = load_checkpoints(args.plan_id) if args.resume else {"subplans": {}}
    existing = load_plan_history(args.plan_id) if args.resume else {}
    if args.resume and existing.get("plan_payload"):
        plan_payload = dict(existing.get("plan_payload") or {})
        subplans = list(plan_payload.get("subplans", []))
        plan_payload.setdefault("resume_contract", {})
        plan_payload["resume_contract"].update(
            {
                "enabled": True,
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
                "resume_mode": "validated_skip_completed_subplans",
                "checkpoint_validation_version": "stage9-v1",
                "invalid_checkpoint_subplans": [],
            }
        )
    else:
        rag6_plan = run_stage_rag6(args)
        subplans = _order_subplans(list(rag6_plan.get("subplans", [])))

        plan_payload = {
            "plan_id": args.plan_id,
            "query": " ".join(args.query),
            "notes": args.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "subplans": subplans,
            "provenance": rag6_plan.get("provenance", {}),
            "reconciliation_contract": {
                "subplan_failure_policy": args.subplan_failure_policy,
                "rollback_model": "delegated_stage6_stage5_bounded_commit",
                "drop_model": "preflight_drop_when_literal_contract_unsupported",
                "checkpoint_model": "persisted_subplan_checkpoints_stage8_v1",
                "rollback_contract_version": "stage9-v1",
            },
            "resume_contract": {
                "enabled": True,
                "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
                "resume_mode": "validated_skip_completed_subplans",
                "checkpoint_validation_version": "stage9-v1",
                "invalid_checkpoint_subplans": [],
            },
        }

        write_plan_history(
            args.plan_id,
            {
                "event_type": "planned",
                "state": "planned",
                "plan_payload": plan_payload,
                "subplan_count": len(subplans),
                "subplan_failure_policy": args.subplan_failure_policy,
            },
        )

    if not subplans:
        write_plan_history(
            args.plan_id,
            {
                "event_type": "plan_empty",
                "state": "no_subplans",
                "plan_payload": plan_payload,
                "statuses": [],
            },
        )
        print("[stage7] no subplans produced, nothing to run")
        return 0

    env = build_promotion_env(lane_name, versions, manifest_cfg.version, manifest_path)
    lane_cfg = versions.get("lane", {})
    statuses: list[dict[str, Any]] = []
    exit_code = 0
    resumed_completed: list[str] = []
    subplans_to_run: list[dict[str, Any]] = []
    strategy_decisions: dict[str, dict[str, Any]] = {}
    hierarchy_contexts: dict[str, dict[str, Any]] = {}
    worker_budget_decisions: list[dict[str, Any]] = []
    family_rescue_usage: dict[str, int] = {}
    manager14_singleton_quota_usage: dict[str, int] = {}
    checkpoint_subplans = checkpoint.get("subplans", {}) if isinstance(checkpoint, dict) else {}
    historical_outcomes = _load_recent_manager6_outcomes(days=args.manager_history_window_days)
    qualification_posture = _load_latest_qualification_posture(max_age_hours=args.qualification_max_age_hours)
    learning_priors = (
        {"active": False, "reason": "learning_priors_disabled"}
        if args.disable_learning_priors
        else _load_learning_priors(
            path=Path(args.learning_priors_path).resolve(),
            max_age_hours=args.learning_priors_max_age_hours,
        )
    )
    task_class = _infer_task_class_from_query(str(plan_payload.get("query") or ""))
    recurrence_memory = _load_cross_run_recurrence_memory(
        task_class=task_class,
        history_window_days=args.manager_history_window_days,
        learning_priors=learning_priors,
    )
    success_memory = _load_cross_run_success_memory(
        task_class=task_class,
        history_window_days=args.manager_history_window_days,
    )
    for subplan in subplans:
        subplan_id = str(subplan.get("subplan_id") or "")
        prior = checkpoint_subplans.get(subplan_id)
        if args.resume and isinstance(prior, dict) and _is_resume_complete_status(str(prior.get("status") or "")):
            valid_checkpoint, checkpoint_issues = _validate_resume_checkpoint_for_subplan(subplan, prior)
            if valid_checkpoint:
                resumed_completed.append(subplan_id)
                resumed_status = {
                    "subplan_id": subplan_id,
                    "status": "resumed_skip_completed",
                    "return_code": 0,
                    "resume_source_status": str(prior.get("status") or ""),
                    "resume_checkpoint_validation": {"ok": True, "issues": []},
                    "strategy": "resume_skip",
                    "targets": prior.get("targets", []),
                    "rollback_contract": prior.get("rollback_contract"),
                    "code_outcomes": {"available": False, "reason": "resume_skip_no_new_dispatch"},
                }
                verification = _verify_rollback_contract_for_status(resumed_status)
                resumed_status["rollback_verification"] = verification
                if verification.get("ok"):
                    statuses.append(resumed_status)
                    continue
                checkpoint_issues = sorted(set(checkpoint_issues + verification.get("issues", [])))
                valid_checkpoint = False
            if not valid_checkpoint:
                plan_payload.setdefault("resume_contract", {}).setdefault("invalid_checkpoint_subplans", []).append(
                    {
                        "subplan_id": subplan_id,
                        "issues": checkpoint_issues,
                    }
                )
        family = _subplan_family_key(subplan)
        budget_class = "grouped" if len(subplan.get("targets", [])) > 1 else "single"
        complexity = _subplan_complexity(subplan)
        budget_limits = _resolve_worker_budget_limits(
            manifest_data=manifest_cfg.data,
            worker_budget_profile=args.worker_budget_profile,
            task_class=task_class,
            complexity=complexity,
            learning_priors=learning_priors,
            grouped_limit=args.worker_budget_grouped,
            single_limit=args.worker_budget_single,
        )
        family_memory = summarize_worker_family_outcomes(
            lane=lane_name,
            worker_class=budget_class,
            family=family,
            window_days=args.manager_memory_window_days,
        )
        forecast = worker_budget_forecast(
            lane=lane_name,
            worker_class=budget_class,
            grouped_limit=int(budget_limits["effective_grouped_limit"]),
            single_limit=int(budget_limits["effective_single_limit"]),
            family=family,
            adaptive_window_days=args.worker_budget_adaptive_window_days,
        )
        forecast["budget_profile"] = budget_limits
        scorecard = _strategy_scorecard(family=family, historical=historical_outcomes)
        strategy_decision = _choose_subplan_strategy(
            subplan=subplan,
            task_class=task_class,
            scorecard=scorecard,
            family_memory=family_memory,
            qualification_posture=qualification_posture,
            budget_forecast=forecast,
            learning_priors=learning_priors,
            success_memory=dict(success_memory.get("families", {}).get(family, {})),
            resume_source_status=str(prior.get("status") or "") if isinstance(prior, dict) else None,
        )
        strategy_decision["recurrence_adaptation"] = {
            "replay_pressure": bool(recurrence_memory.get("replay_pressure")),
            "conservative_split": bool(recurrence_memory.get("conservative_split")),
            "recent_bad_rate": float(recurrence_memory.get("recent_bad_rate") or 0.0),
        }
        strategy_decision["family"] = family
        strategy_decision["budget_profile"] = budget_limits
        strategy_decisions[subplan_id] = strategy_decision
        subplans_to_run.append(subplan)

    hierarchical_plan = _build_hierarchical_decomposition(
        subplans_to_run,
        recurrence_memory=recurrence_memory,
    )
    subplans_to_run = list(hierarchical_plan.get("ordered_subplans") or subplans_to_run)
    subplans_to_run, predispatch_shaping = _apply_manager13_predispatch_shaping(
        subplans=subplans_to_run,
        strategy_decisions=strategy_decisions,
        recurrence_memory=recurrence_memory,
    )
    manager14_budget_fallback = _apply_manager14_budget_fallback_shaping(
        subplans=subplans_to_run,
        strategy_decisions=strategy_decisions,
        recurrence_memory=recurrence_memory,
    )
    hierarchy_contexts = {
        str(k): dict(v)
        for k, v in (hierarchical_plan.get("contexts") or {}).items()
        if str(k)
    }
    for subplan in subplans_to_run:
        subplan_id = str(subplan.get("subplan_id") or "")
        if not subplan_id:
            continue
        if subplan_id in hierarchy_contexts:
            strategy_decisions.setdefault(subplan_id, {}).update(
                {"hierarchy_context": hierarchy_contexts[subplan_id]}
            )

    plan_payload.setdefault("manager_decisions", {})
    plan_payload["manager_decisions"].update(
        {
            "strategy_decisions": strategy_decisions,
            "hierarchical_decomposition": {
                "cohorts": list(hierarchical_plan.get("cohorts") or []),
                "summary": dict(hierarchical_plan.get("summary") or {}),
                "strategy": (
                    "manager14_budget_fallback_predispatch_hierarchy"
                    if bool(manager14_budget_fallback.get("enabled"))
                    else (
                        "manager13_proactive_predispatch_recurrence_shaping"
                        if bool(predispatch_shaping.get("enabled"))
                        else (
                            "manager12_recurrence_aware_hierarchical_repackaging"
                            if bool(recurrence_memory.get("replay_pressure"))
                            or bool(recurrence_memory.get("conservative_split"))
                            else "manager11_hierarchical_two_level"
                        )
                    )
                ),
            },
            "predispatch_shaping": predispatch_shaping,
            "manager14_budget_fallback": manager14_budget_fallback,
            "manager15_success_memory": {
                "task_class": str(success_memory.get("task_class") or task_class),
                "history_rows": int(success_memory.get("history_rows") or 0),
                "families_with_preferences": int(
                    sum(
                        1
                        for row in (success_memory.get("families") or {}).values()
                        if isinstance(row, dict) and str(row.get("preferred_strategy") or "")
                    )
                ),
            },
            "manager_version": "manager15-v1",
            "history_window_days": args.manager_history_window_days,
            "memory_window_days": args.manager_memory_window_days,
            "family_rescue_budget": args.family_rescue_budget,
            "recurrence_memory": recurrence_memory,
            "qualification_posture": qualification_posture,
            "learning_priors": {
                "active": bool(learning_priors.get("active")),
                "reason": str(learning_priors.get("reason") or ""),
                "path": str(learning_priors.get("path") or ""),
                "generated_at_utc": str(learning_priors.get("generated_at_utc") or ""),
                "age_hours": learning_priors.get("age_hours"),
                "weak_classes": list(learning_priors.get("weak_classes") or []),
                "recurrence_pressure": bool(learning_priors.get("recurrence_pressure")),
                "benchmark_escalation_rate": float(learning_priors.get("benchmark_escalation_rate") or 0.0),
                "benchmark_first_attempt_quality_rate": float(
                    learning_priors.get("benchmark_first_attempt_quality_rate") or 0.0
                ),
            },
        }
    )

    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_resumed" if args.resume else "attempt_started",
            "decision_state": "evaluate->choose_strategy->execute",
            "state": "running",
            "plan_payload": plan_payload,
            "statuses": statuses if args.resume else [],
            "resume_completed_subplans": resumed_completed,
        },
    )

    for idx, subplan in enumerate(subplans_to_run):
        subplan_id = str(subplan.get("subplan_id") or f"subplan-{idx + 1}")
        strategy_decision = strategy_decisions.get(subplan_id, {"strategy": "run_grouped", "reason": "default_grouped"})
        family = str(strategy_decision.get("family") or _subplan_family_key(subplan))
        target_count = len([str(t) for t in subplan.get("targets", []) if t])
        budget_class = "grouped" if len(subplan.get("targets", [])) > 1 else "single"
        if strategy_decision.get("strategy") == "defer_manual":
            preemptive_budget = {
                "lane": lane_name,
                "worker_class": budget_class,
                "allowed": False,
                "reason": "manager9_preemptive_defer",
                "forecast": strategy_decision.get("budget_forecast", {}),
                "budget_profile": strategy_decision.get("budget_profile", {}),
            }
            worker_budget_decisions.append(preemptive_budget)
            status = {
                "subplan_id": subplan_id,
                "targets": [str(t) for t in subplan.get("targets", []) if t],
                "target_contracts": [],
                "dropped_targets": [],
                "status": "deferred_manager_policy",
                "return_code": 0,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "strategy": "defer_manual",
                "strategy_decision": strategy_decision,
                "worker_budget_decision": preemptive_budget,
                "escalation_hint": "manual_lane_manager9_preemptive_defer",
                "rollback_contract": {
                    "contract_version": "stage9-v1",
                    "strategy": "manager9_preemptive_defer_no_dispatch",
                    "rollback_scope": [],
                    "trigger_on_failure": False,
                    "verification": "not_applicable_no_dispatch",
                    "notes": "Manager-9 deferred subplan before dispatch due to qualification/budget posture.",
                },
                "code_outcomes": {"available": False, "reason": "manager_preemptive_defer_no_dispatch"},
            }
            statuses.append(status)
            record_worker_outcome(
                lane=lane_name,
                worker_class=budget_class,
                family=family,
                status=str(status.get("status") or "unknown"),
                escalation_hint=str(status.get("escalation_hint") or ""),
            )
            save_checkpoint(args.plan_id, status, attempt_index=idx + 1)
            continue
        budget_decision: WorkerBudgetDecision = apply_worker_budget(
            lane=lane_name,
            worker_class=budget_class,
            grouped_limit=int(strategy_decision.get("budget_profile", {}).get("effective_grouped_limit", args.worker_budget_grouped)),
            single_limit=int(strategy_decision.get("budget_profile", {}).get("effective_single_limit", args.worker_budget_single)),
            family=family,
            adaptive_window_days=args.worker_budget_adaptive_window_days,
        )
        budget_decision_payload = budget_decision.to_dict()
        budget_decision_payload["budget_profile"] = strategy_decision.get("budget_profile", {})
        learning_override_used = False
        manager14_singleton_carryover_used = False
        if (
            not budget_decision.allowed
            and target_count == 1
            and "learning_priors" in set(strategy_decision.get("decision_tags") or [])
            and int(family_rescue_usage.get(family, 0)) < 1
        ):
            learning_override_used = True
            family_rescue_usage[family] = int(family_rescue_usage.get(family, 0)) + 1
            budget_decision_payload.update(
                {
                    "allowed": True,
                    "reason": "manager10_learning_prior_budget_override",
                    "learning_override_used": True,
                }
            )
        if not budget_decision_payload.get("allowed") and target_count == 1:
            manager14_enabled = bool(strategy_decision.get("manager14_budget_fallback_enabled"))
            target_meta = subplan.get("target_meta") if isinstance(subplan.get("target_meta"), list) else []
            risk_rank = max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in target_meta), default=2)
            family_budget_remaining = int(args.family_rescue_budget) - int(family_rescue_usage.get(family, 0))
            recurrence_adaptation = (
                strategy_decision.get("recurrence_adaptation")
                if isinstance(strategy_decision.get("recurrence_adaptation"), dict)
                else {}
            )
            replay_pressure = bool(recurrence_adaptation.get("replay_pressure"))
            recent_bad_rate = float(recurrence_adaptation.get("recent_bad_rate") or 0.0)
            singleton_quota_cap = (
                1
                if manager14_enabled
                and (replay_pressure or recent_bad_rate >= 0.35)
                and task_class in {"multi_file_orchestration", "retrieval_orchestration", "resumable_checkpointed"}
                else 0
            )
            if (
                manager14_enabled
                and risk_rank <= 1
                and family_budget_remaining > 0
            ):
                manager14_singleton_carryover_used = True
                family_rescue_usage[family] = int(family_rescue_usage.get(family, 0)) + 1
                budget_decision_payload.update(
                    {
                        "allowed": True,
                        "reason": "manager14_singleton_budget_carryover_override",
                        "manager14_singleton_budget_carryover_used": True,
                        "manager14_singleton_budget_carryover_risk_rank": int(risk_rank),
                        "manager14_singleton_budget_carryover_family_budget_remaining": int(
                            family_budget_remaining - 1
                        ),
                    }
                )
            elif (
                manager14_enabled
                and risk_rank <= 1
                and int(manager14_singleton_quota_usage.get(family, 0)) < singleton_quota_cap
            ):
                manager14_singleton_quota_usage[family] = int(manager14_singleton_quota_usage.get(family, 0)) + 1
                manager14_singleton_carryover_used = True
                budget_decision_payload.update(
                    {
                        "allowed": True,
                        "reason": "manager14_singleton_low_risk_dispatch_quota",
                        "manager14_singleton_budget_carryover_used": True,
                        "manager14_singleton_budget_carryover_risk_rank": int(risk_rank),
                        "manager14_singleton_low_risk_dispatch_quota_used": True,
                        "manager14_singleton_low_risk_dispatch_quota_remaining": int(
                            max(0, singleton_quota_cap - int(manager14_singleton_quota_usage.get(family, 0)))
                        ),
                    }
                )
        worker_budget_decisions.append(budget_decision_payload)
        if not budget_decision_payload.get("allowed"):
            manager14_fallback_enabled = bool(strategy_decision.get("manager14_budget_fallback_enabled"))
            if manager14_fallback_enabled and target_count > 1:
                split_statuses: list[dict[str, Any]] = []
                split_success = True
                split_dispatched = 0
                targets = [str(t) for t in subplan.get("targets", []) if t]
                target_meta_entries = (
                    subplan.get("target_meta") if isinstance(subplan.get("target_meta"), list) else []
                )
                target_risk_by_path = {
                    str(entry.get("path")): _risk_rank(str(entry.get("risk_bucket") or "high"))
                    for entry in target_meta_entries
                    if isinstance(entry, dict) and entry.get("path")
                }
                target_risk_by_name = {
                    Path(path).name: int(rank) for path, rank in target_risk_by_path.items() if path
                }
                grouped_carryover_used = 0
                grouped_family_budget_remaining = max(
                    0,
                    int(args.family_rescue_budget) - int(family_rescue_usage.get(family, 0)),
                )
                grouped_carryover_cap = min(2, grouped_family_budget_remaining)
                recurrence_adaptation = (
                    strategy_decision.get("recurrence_adaptation")
                    if isinstance(strategy_decision.get("recurrence_adaptation"), dict)
                    else {}
                )
                replay_pressure = bool(recurrence_adaptation.get("replay_pressure"))
                predispatch_shape = (
                    strategy_decision.get("predispatch_shape")
                    if isinstance(strategy_decision.get("predispatch_shape"), dict)
                    else {}
                )
                scorecard = (
                    strategy_decision.get("scorecard")
                    if isinstance(strategy_decision.get("scorecard"), dict)
                    else {}
                )
                family_bad_rate = float(predispatch_shape.get("family_bad_rate") or 0.0)
                grouped_bad_rate = float(predispatch_shape.get("grouped_bad_rate") or 0.0)
                grouped_rate = float(scorecard.get("grouped_rate") or 0.0)
                split_rate = float(scorecard.get("split_rate") or 0.0)
                all_low_risk_targets = bool(targets) and all(
                    int(target_risk_by_path.get(path, 2)) <= 1 for path in targets
                )
                split_history_favors_singletons = (
                    split_rate >= 0.8 and (split_rate - grouped_rate) >= 0.2
                )
                bounded_low_risk_split_relief = (
                    grouped_carryover_cap == 0
                    and task_class in {"multi_file_orchestration", "retrieval_orchestration"}
                    and str(strategy_decision.get("strategy") or "") == "split_first"
                    and len(targets) <= 2
                    and all_low_risk_targets
                    and grouped_bad_rate <= 0.2
                    and (
                        family_bad_rate <= 0.26
                        or (family_bad_rate <= 0.6 and split_history_favors_singletons)
                    )
                )
                low_risk_dispatch_quota_cap = (
                    1
                    if grouped_carryover_cap == 0
                    and (
                        replay_pressure
                        or bounded_low_risk_split_relief
                    )
                    and task_class in {"multi_file_orchestration", "retrieval_orchestration", "bounded_architecture"}
                    else 0
                )
                # Bounded extension: for tiny low-risk grouped orchestration subplans with
                # favorable recurrence trends, allow one additional singleton dispatch.
                if (
                    low_risk_dispatch_quota_cap == 1
                    and len(targets) <= 2
                    and all_low_risk_targets
                    and family_bad_rate <= 0.3
                    and grouped_bad_rate <= 0.35
                ):
                    low_risk_dispatch_quota_cap = 2
                # When split history clearly dominates grouped history for a tiny
                # low-risk subplan, allow dispatch of both singleton splits.
                if (
                    low_risk_dispatch_quota_cap < 2
                    and bounded_low_risk_split_relief
                    and split_history_favors_singletons
                    and grouped_bad_rate <= 0.16
                ):
                    low_risk_dispatch_quota_cap = 2
                strict_first_attempt_mode = (
                    str(args.subplan_failure_policy or "") == "abort"
                    and int(args.family_rescue_budget) <= 0
                )
                quota_risk_rank_limit = 1
                if (
                    strict_first_attempt_mode
                    and low_risk_dispatch_quota_cap > 0
                    and split_history_favors_singletons
                    and task_class in {"multi_file_orchestration", "retrieval_orchestration", "bounded_architecture"}
                    and len(targets) <= 2
                    and family_bad_rate <= 0.35
                    and grouped_bad_rate <= 0.15
                ):
                    # Bounded extension for first-attempt-only pressure:
                    # allow a single medium-risk singleton dispatch when recurrence
                    # history strongly favors split execution.
                    quota_risk_rank_limit = 2
                low_risk_targets = sum(1 for path in targets if int(target_risk_by_path.get(path, 2)) <= 1)
                medium_or_lower_targets = sum(
                    1 for path in targets if int(target_risk_by_path.get(path, 2)) <= 2
                )
                if (
                    strict_first_attempt_mode
                    and low_risk_dispatch_quota_cap == 1
                    and task_class in {"retrieval_orchestration", "bounded_architecture"}
                    and len(targets) <= 2
                    and low_risk_targets >= 1
                    and medium_or_lower_targets == len(targets)
                    and family_bad_rate <= 0.35
                    and grouped_bad_rate <= 0.2
                ):
                    # Shared edge blocker fix: tiny low/medium mixed-family grouped
                    # pairs were exhausting a single quota dispatch and then deferring.
                    # Under strict first-attempt constraints, allow dispatch of both
                    # singleton splits while preserving bounded risk guards.
                    low_risk_dispatch_quota_cap = 2
                    quota_risk_rank_limit = 2
                low_risk_dispatch_quota_used = 0
                for split_idx, target_path in enumerate(targets, start=1):
                    single_budget_decision = apply_worker_budget(
                        lane=lane_name,
                        worker_class="single",
                        grouped_limit=int(
                            strategy_decision.get("budget_profile", {}).get(
                                "effective_grouped_limit", args.worker_budget_grouped
                            )
                        ),
                        single_limit=int(
                            strategy_decision.get("budget_profile", {}).get(
                                "effective_single_limit", args.worker_budget_single
                            )
                        ),
                        family=family,
                        adaptive_window_days=args.worker_budget_adaptive_window_days,
                    )
                    single_budget_payload = single_budget_decision.to_dict()
                    single_budget_payload["budget_profile"] = strategy_decision.get("budget_profile", {})
                    single_budget_payload["manager14_budget_fallback"] = True
                    single_override_used = False
                    used_low_risk_quota = False
                    if not single_budget_payload.get("allowed"):
                        target_risk_rank = int(
                            target_risk_by_path.get(
                                target_path,
                                target_risk_by_name.get(Path(target_path).name, 2),
                            )
                        )
                        family_budget_remaining = int(args.family_rescue_budget) - int(
                            family_rescue_usage.get(family, 0)
                        )
                        if (
                            target_risk_rank <= 1
                            and family_budget_remaining > 0
                            and grouped_carryover_used < grouped_carryover_cap
                        ):
                            single_override_used = True
                            grouped_carryover_used += 1
                            family_rescue_usage[family] = int(family_rescue_usage.get(family, 0)) + 1
                            single_budget_payload.update(
                                {
                                    "allowed": True,
                                    "reason": "manager14_grouped_budget_carryover_override",
                                    "manager14_grouped_budget_carryover_used": True,
                                    "manager14_grouped_budget_carryover_risk_rank": int(target_risk_rank),
                                    "manager14_grouped_budget_carryover_family_budget_remaining": int(
                                        family_budget_remaining - 1
                                    ),
                                }
                            )
                        elif (
                            target_risk_rank <= quota_risk_rank_limit
                            and low_risk_dispatch_quota_used < low_risk_dispatch_quota_cap
                        ):
                            single_override_used = True
                            used_low_risk_quota = True
                            low_risk_dispatch_quota_used += 1
                            single_budget_payload.update(
                                {
                                    "allowed": True,
                                    "reason": "manager14_grouped_low_risk_dispatch_quota",
                                    "manager14_grouped_budget_carryover_used": True,
                                    "manager14_grouped_budget_carryover_risk_rank": int(target_risk_rank),
                                    "manager14_grouped_low_risk_dispatch_quota_used": True,
                                    "manager14_grouped_low_risk_dispatch_quota_remaining": int(
                                        max(0, low_risk_dispatch_quota_cap - low_risk_dispatch_quota_used)
                                    ),
                                    "manager14_grouped_low_risk_dispatch_quota_risk_rank_limit": int(
                                        quota_risk_rank_limit
                                    ),
                                    "manager14_grouped_low_risk_dispatch_quota_first_attempt_mode": bool(
                                        strict_first_attempt_mode
                                    ),
                                }
                            )
                    worker_budget_decisions.append(single_budget_payload)

                    if not single_budget_payload.get("allowed"):
                        bounded_partial_drop_allowed = (
                            split_dispatched > 0
                            and target_risk_rank <= 1
                            and replay_pressure
                            and task_class in {"multi_file_orchestration", "retrieval_orchestration"}
                            and grouped_bad_rate <= 0.2
                        )
                        if bounded_partial_drop_allowed:
                            split_status = {
                                "subplan_id": f"{subplan_id}-manager14-{split_idx}",
                                "targets": [target_path],
                                "target_contracts": [],
                                "dropped_targets": [target_path],
                                "status": "dropped_preflight",
                                "return_code": 0,
                                "started_at": datetime.now(timezone.utc).isoformat(),
                                "finished_at": datetime.now(timezone.utc).isoformat(),
                                "strategy": "manager14_singleton_fallback_drop",
                                "strategy_decision": {
                                    **dict(strategy_decision),
                                    "manager14_budget_fallback_used": True,
                                    "manager14_budget_fallback_reason": "singleton_budget_bounded_partial_drop",
                                },
                                "worker_budget_decision": single_budget_payload,
                                "escalation_hint": "",
                                "rollback_contract": {
                                    "contract_version": "stage9-v1",
                                    "strategy": "manager14_singleton_fallback_bounded_drop",
                                    "rollback_scope": [],
                                    "trigger_on_failure": False,
                                    "verification": "not_applicable_no_dispatch",
                                    "notes": "Manager-14 performed bounded low-risk partial drop after successful singleton dispatch.",
                                },
                                "code_outcomes": {
                                    "available": False,
                                    "reason": "worker_budget_bounded_partial_drop",
                                },
                            }
                        else:
                            split_status = {
                                "subplan_id": f"{subplan_id}-manager14-{split_idx}",
                                "targets": [target_path],
                                "target_contracts": [],
                                "dropped_targets": [],
                                "status": "deferred_worker_budget",
                                "return_code": 0,
                                "started_at": datetime.now(timezone.utc).isoformat(),
                                "finished_at": datetime.now(timezone.utc).isoformat(),
                                "strategy": "manager14_singleton_fallback_defer",
                                "strategy_decision": {
                                    **dict(strategy_decision),
                                    "manager14_budget_fallback_used": True,
                                    "manager14_budget_fallback_reason": "singleton_budget_exhausted",
                                },
                                "worker_budget_decision": single_budget_payload,
                                "escalation_hint": "manual_lane_budget_exhausted_singleton_fallback",
                                "rollback_contract": {
                                    "contract_version": "stage9-v1",
                                    "strategy": "manager14_singleton_fallback_no_dispatch",
                                    "rollback_scope": [],
                                    "trigger_on_failure": False,
                                    "verification": "not_applicable_no_dispatch",
                                    "notes": "Manager-14 singleton fallback exhausted single worker budget.",
                                },
                                "code_outcomes": {"available": False, "reason": "worker_budget_defer_no_dispatch"},
                            }
                    else:
                        split_dispatched += 1
                        split_status = run_stage6_subplan(
                            subplan={"subplan_id": f"{subplan_id}-manager14-{split_idx}", "targets": [target_path]},
                            args=args,
                            env=env,
                            op_index=(idx * 100) + split_idx,
                            strategy_tag="manager14_singleton_fallback",
                            strategy_decision={
                                **dict(strategy_decision),
                                "manager14_budget_fallback_used": True,
                                "manager14_budget_fallback_reason": (
                                    "grouped_budget_to_singleton_dispatch_via_carryover"
                                    if single_override_used and not used_low_risk_quota
                                    else (
                                        "grouped_budget_to_singleton_dispatch_via_low_risk_quota"
                                        if single_override_used and used_low_risk_quota
                                        else "grouped_budget_to_singleton_dispatch"
                                    )
                                ),
                            },
                        )
                        split_status["worker_budget_decision"] = single_budget_payload
                    split_verification = _verify_rollback_contract_for_status(split_status)
                    split_status["rollback_verification"] = split_verification
                    if not split_verification.get("ok"):
                        split_status["status"] = "rollback_contract_invalid"
                        split_status["return_code"] = 1
                        split_status["failure_reason"] = "stage9_rollback_contract_verification_failed"
                        split_success = False
                    if int(split_status.get("return_code") or 0) != 0:
                        split_success = False
                    split_statuses.append(split_status)

                for split_checkpoint_idx, split_status in enumerate(split_statuses, start=1):
                    record_worker_outcome(
                        lane=lane_name,
                        worker_class="single",
                        family=family,
                        status=str(split_status.get("status") or "unknown"),
                        escalation_hint=str(split_status.get("escalation_hint") or ""),
                    )
                    save_checkpoint(
                        args.plan_id,
                        split_status,
                        attempt_index=(idx + 1) * 100 + split_checkpoint_idx,
                    )
                statuses.extend(split_statuses)
                plan_payload.setdefault("recoveries", []).append(
                    {
                        "failed_subplan": subplan_id,
                        "strategy": "manager14_budget_constrained_singleton_fallback",
                        "split_count": len(split_statuses),
                        "dispatched_count": split_dispatched,
                        "manager14_grouped_carryover_dispatches": grouped_carryover_used,
                        "result": "success" if split_success and split_dispatched > 0 else "partial_or_failed",
                        "decision_state": "evaluate->budget_fallback_split->reconcile",
                    }
                )
                if split_success and split_dispatched > 0:
                    continue
                status = {
                    "subplan_id": subplan_id,
                    "targets": targets,
                    "target_contracts": [],
                    "dropped_targets": [],
                    "status": "deferred_worker_budget",
                    "return_code": 0,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "strategy": "defer_manual",
                    "strategy_decision": {
                        **dict(strategy_decision),
                        "manager14_budget_fallback_used": True,
                        "manager14_budget_fallback_reason": "all_singleton_dispatches_blocked_or_failed",
                    },
                    "worker_budget_decision": budget_decision_payload,
                    "escalation_hint": "manual_lane_budget_exhausted",
                    "rollback_contract": {
                        "contract_version": "stage9-v1",
                        "strategy": "manager14_singleton_fallback_exhausted",
                        "rollback_scope": [],
                        "trigger_on_failure": False,
                        "verification": "not_applicable_no_dispatch",
                        "notes": "Manager-14 fallback could not dispatch enough singleton work.",
                    },
                    "code_outcomes": {"available": False, "reason": "worker_budget_defer_no_dispatch"},
                }
            else:
                status = {
                    "subplan_id": subplan_id,
                    "targets": [str(t) for t in subplan.get("targets", []) if t],
                    "target_contracts": [],
                    "dropped_targets": [],
                    "status": "deferred_worker_budget",
                    "return_code": 0,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "strategy": "defer_manual",
                    "strategy_decision": strategy_decision,
                    "worker_budget_decision": budget_decision_payload,
                    "escalation_hint": "manual_lane_budget_exhausted",
                    "rollback_contract": {
                        "contract_version": "stage9-v1",
                        "strategy": "no_dispatch_budget_exhausted",
                        "rollback_scope": [],
                        "trigger_on_failure": False,
                        "verification": "not_applicable_no_dispatch",
                        "notes": "Worker budget exhausted before subplan dispatch.",
                    },
                    "code_outcomes": {"available": False, "reason": "worker_budget_defer_no_dispatch"},
                }
        elif strategy_decision.get("strategy") == "split_first" and len(subplan.get("targets", [])) > 1:
            split_success, split_statuses = _run_split_recovery(
                failed_subplan={"subplan_id": subplan_id, "targets": subplan.get("targets", [])},
                args=args,
                env=env,
                statuses=statuses,
            )
            for split_status in split_statuses:
                split_status["strategy"] = "split_subplan"
                split_status["strategy_decision"] = strategy_decision
                split_status["worker_budget_decision"] = budget_decision_payload
                split_verification = _verify_rollback_contract_for_status(split_status)
                split_status["rollback_verification"] = split_verification
                if not split_verification.get("ok"):
                    split_status["status"] = "rollback_contract_invalid"
                    split_status["return_code"] = 1
                    split_status["failure_reason"] = "stage9_rollback_contract_verification_failed"
                    all_success = False
                record_worker_outcome(
                    lane=lane_name,
                    worker_class=budget_class,
                    family=family,
                    status=str(split_status.get("status") or "unknown"),
                    escalation_hint=str(split_status.get("escalation_hint") or ""),
                )
            statuses.extend(split_statuses)
            for split_idx, split_status in enumerate(split_statuses, start=1):
                save_checkpoint(args.plan_id, split_status, attempt_index=(idx + 1) * 100 + split_idx)
            plan_payload.setdefault("recoveries", []).append(
                {
                    "failed_subplan": subplan_id,
                    "strategy": "split_first",
                    "split_count": len(split_statuses),
                    "result": "success" if split_success else "partial_or_failed",
                    "decision_state": "choose_strategy->split_first->reconcile",
                }
            )
            if not split_success:
                if family_rescue_usage.get(family, 0) >= args.family_rescue_budget:
                    status = {
                        "subplan_id": subplan_id,
                        "targets": [str(t) for t in subplan.get("targets", []) if t],
                        "target_contracts": [],
                        "dropped_targets": [],
                        "status": "dropped_family_budget",
                        "return_code": 0,
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "strategy": "drop",
                        "strategy_decision": strategy_decision,
                        "worker_budget_decision": budget_decision_payload,
                        "rollback_contract": {
                            "contract_version": "stage9-v1",
                            "strategy": "drop_after_family_budget_exhaustion",
                            "rollback_scope": [],
                            "trigger_on_failure": False,
                            "verification": "not_applicable_no_dispatch",
                            "notes": "Family rescue budget exhausted.",
                        },
                        "code_outcomes": {"available": False, "reason": "family_budget_drop_no_dispatch"},
                    }
                    family_rescue_usage[family] = family_rescue_usage.get(family, 0) + 1
                else:
                    exit_code = 1
                    break
            else:
                continue
        else:
            status = run_stage6_subplan(
                subplan=subplan,
                args=args,
                env=env,
                op_index=idx,
                strategy_tag="grouped_subplan",
                strategy_decision=strategy_decision,
            )
            status["worker_budget_decision"] = budget_decision_payload
            if learning_override_used:
                status["strategy_decision"] = {
                    **dict(status.get("strategy_decision") or {}),
                    "learning_budget_override_used": True,
                }
            if manager14_singleton_carryover_used:
                status["strategy_decision"] = {
                    **dict(status.get("strategy_decision") or {}),
                    "manager14_singleton_budget_carryover_used": True,
                }
        statuses.append(status)
        rollback_verification = _verify_rollback_contract_for_status(status)
        status["rollback_verification"] = rollback_verification
        if not rollback_verification.get("ok"):
            status["status"] = "rollback_contract_invalid"
            status["return_code"] = 1
            status["failure_reason"] = "stage9_rollback_contract_verification_failed"
            exit_code = 1
            save_checkpoint(args.plan_id, status, attempt_index=idx + 1)
            break
        record_worker_outcome(
            lane=lane_name,
            worker_class=budget_class,
            family=family,
            status=str(status.get("status") or "unknown"),
            escalation_hint=str(status.get("escalation_hint") or ""),
        )
        save_checkpoint(args.plan_id, status, attempt_index=idx + 1)

        if args.stop_after_subplans > 0 and (idx + 1) >= args.stop_after_subplans:
            plan_payload.setdefault("resume_events", []).append(
                {
                    "event": "paused_by_operator",
                    "processed_subplans": idx + 1,
                    "remaining_subplans": max(len(subplans_to_run) - (idx + 1), 0),
                    "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
                }
            )
            write_plan_history(
                args.plan_id,
                {
                    "event_type": "attempt_paused",
                    "decision_state": "execute->paused",
                    "state": "paused",
                    "statuses": statuses,
                    "plan_payload": plan_payload,
                    "failure_code": 0,
                },
            )
            trace = PromotionTraceEntry(
                lane=lane_name,
                lane_label=lane_cfg.get("label", "Stage-7 preview lane"),
                lane_status=lane_cfg.get("status", "preview"),
                lane_reason=f"plan:{args.plan_id}",
                stage=versions.get("stage"),
                stage_version=versions.get("stage_version_name"),
                manager_version=versions.get("manager_version_name"),
                rag_version=versions.get("rag_version_name"),
                promotion_policy_status=args.plan_status,
                manifest_version=manifest_cfg.version,
                manifest_path=str(manifest_path),
                literal_lines=0,
                return_code=0,
                promotion_outcome="paused",
                commit_hash=current_commit_hash(),
                extra={"plan_id": args.plan_id, "subplans": statuses, "plan_payload": plan_payload, "resume": args.resume},
            )
            append_trace(trace, trace_dir=TRACE_DIR)
            print(
                f"[stage7] paused after {idx + 1} subplan(s); checkpoints saved to {plan_checkpoint_path(args.plan_id)}"
            )
            return 0

        if status["return_code"] == 0:
            continue

        if args.subplan_failure_policy == "continue":
            plan_payload.setdefault("drops", []).append(
                {
                    "subplan_id": status["subplan_id"],
                    "targets": status.get("targets", []),
                    "reason": "subplan_failed_continue_policy",
                }
            )
            continue

        if args.subplan_failure_policy == "split_on_failure" and len(status.get("targets", [])) > 1:
            split_success, split_statuses = _run_split_recovery(
                failed_subplan=status,
                args=args,
                env=env,
                statuses=statuses,
            )
            for split_status in split_statuses:
                split_verification = _verify_rollback_contract_for_status(split_status)
                split_status["rollback_verification"] = split_verification
                if not split_verification.get("ok"):
                    split_status["status"] = "rollback_contract_invalid"
                    split_status["return_code"] = 1
                    split_status["failure_reason"] = "stage9_rollback_contract_verification_failed"
                    split_success = False
            statuses.extend(split_statuses)
            for split_idx, split_status in enumerate(split_statuses, start=1):
                save_checkpoint(args.plan_id, split_status, attempt_index=(idx + 1) * 100 + split_idx)
            plan_payload.setdefault("recoveries", []).append(
                {
                    "failed_subplan": status["subplan_id"],
                    "strategy": "split_on_failure",
                    "split_count": len(split_statuses),
                    "result": "success" if split_success else "partial_or_failed",
                    "decision_state": "execute->split_on_failure->reconcile",
                }
            )
            if split_success:
                continue

        exit_code = int(status["return_code"])
        if args.subplan_failure_policy == "abort":
            break

    final_state = "succeeded" if exit_code == 0 else "failed"
    if exit_code == 0 and (plan_payload.get("drops") or plan_payload.get("recoveries")):
        final_state = "partial_success"
    plan_payload.setdefault("manager_decisions", {})
    plan_payload["manager_decisions"]["worker_budget_decisions"] = worker_budget_decisions
    rollback_checks = [s.get("rollback_verification") for s in statuses if isinstance(s.get("rollback_verification"), dict)]
    rollback_ok = sum(1 for item in rollback_checks if item.get("ok"))
    rollback_fail = len(rollback_checks) - rollback_ok
    coverage = _subplan_coverage_summary(subplans, statuses)
    plan_payload.setdefault("stage_reconciliation", {})
    plan_payload["stage_reconciliation"] = {
        "stage_version": "stage9-v1",
        "resume_mode": plan_payload.get("resume_contract", {}).get("resume_mode"),
        "rollback_contract_verification": {
            "checked": len(rollback_checks),
            "ok": rollback_ok,
            "failed": rollback_fail,
            "all_verified": rollback_fail == 0,
        },
        "subplan_coverage": coverage,
        "outcome_guarantee": {
            "all_subplans_accounted": bool(coverage.get("coverage_ok")),
            "all_checked_contracts_valid": rollback_fail == 0,
        },
    }

    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_finished",
            "decision_state": "execute->reconcile->finished",
            "state": final_state,
            "statuses": statuses,
            "failure_code": exit_code,
            "plan_payload": plan_payload,
        },
    )

    trace = PromotionTraceEntry(
        lane=lane_name,
        lane_label=lane_cfg.get("label", "Stage-7 preview lane"),
        lane_status=lane_cfg.get("status", "preview"),
        lane_reason=f"plan:{args.plan_id}",
        stage=versions.get("stage"),
        stage_version=versions.get("stage_version_name"),
        manager_version=versions.get("manager_version_name"),
        rag_version=versions.get("rag_version_name"),
        promotion_policy_status=args.plan_status,
        manifest_version=manifest_cfg.version,
        manifest_path=str(manifest_path),
        literal_lines=0,
        return_code=exit_code,
        promotion_outcome="success" if exit_code == 0 else "failure",
        commit_hash=current_commit_hash(),
        extra={
            "plan_id": args.plan_id,
            "subplans": statuses,
            "plan_payload": plan_payload,
            "resume": args.resume,
            "resume_completed_subplans": resumed_completed,
            "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
            "manager_decisions": plan_payload.get("manager_decisions", {}),
        },
    )
    append_trace(trace, trace_dir=TRACE_DIR)

    if exit_code == 0:
        print(f"[stage7] orchestrated {len(statuses)} subplan execution(s) for plan {args.plan_id}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
