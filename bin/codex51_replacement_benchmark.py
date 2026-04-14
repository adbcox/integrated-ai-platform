#!/usr/bin/env python3
"""Executable Codex 5.1 replacement benchmark over local stage/manager artifacts."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "config" / "codex51_replacement_benchmark.json"
DEFAULT_PLAN_DIR = REPO_ROOT / "artifacts" / "manager6" / "plans"
DEFAULT_CAMPAIGN_RUNS = REPO_ROOT / "artifacts" / "codex51" / "campaign" / "runs.jsonl"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "codex51" / "benchmark"

SUCCESS_STATUSES = {"success", "resumed_skip_completed"}


@dataclass
class PlanRun:
    plan_id: str
    timestamp: str
    query: str
    class_id: str
    class_label: str
    ranking_version: str
    state: str
    failure_code: int
    total_subplans: int
    first_attempt_success: int
    first_attempt_quality_rate: float
    rescue_count: int
    escalation_count: int
    guard_count: int
    success: bool
    failure_signature: str
    attribution_profile: str
    attribution_primary: str


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sorted_targets(items: Any) -> list[str]:
    return sorted({str(x) for x in (items or []) if x})


def classify_class(query: str, class_rules: list[dict[str, Any]]) -> tuple[str, str]:
    query_l = query.lower()
    for rule in class_rules:
        tokens = [str(t).lower() for t in rule.get("query_any", []) if str(t).strip()]
        if tokens and any(token in query_l for token in tokens):
            return str(rule.get("class_id") or "unclassified"), str(rule.get("label") or "Unclassified")
    return "unclassified", "Unclassified"


def _status_failure_signature(statuses: list[dict[str, Any]]) -> str:
    signatures: list[str] = []
    for row in statuses:
        status = str(row.get("status") or "")
        if status in SUCCESS_STATUSES or status == "dropped_preflight":
            continue
        reason = str(row.get("failure_reason") or "")
        if reason:
            signatures.append(f"{status}:{reason}")
        else:
            signatures.append(status or "unknown")
    if not signatures:
        return ""
    return "|".join(sorted(set(signatures)))


def _primary_attribution_label(
    *,
    success: bool,
    rescue_count: int,
    guard_count: int,
    ranking_version: str,
    first_attempt_quality_rate: float,
) -> str:
    if success and first_attempt_quality_rate >= 1.0 and rescue_count == 0 and guard_count == 0:
        return "model_gain"
    if success and rescue_count > 0:
        return "manager_gain"
    if success and ranking_version.startswith("rag9"):
        return "retrieval_gain"
    if guard_count > 0:
        return "guard_policy_gain"
    return "mixed_gain"


def _load_campaign_profiles(campaign_runs_path: Path) -> dict[str, str]:
    if not campaign_runs_path.exists():
        return {}
    profile_by_plan: dict[str, str] = {}
    with campaign_runs_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            plan_id = str(row.get("plan_id") or "")
            profile = str(row.get("attribution_profile") or "")
            if plan_id and profile:
                profile_by_plan[plan_id] = profile
    return profile_by_plan


def load_plan_runs(
    *,
    plan_dir: Path,
    class_rules: list[dict[str, Any]],
    window_days: int,
    campaign_profiles: dict[str, str],
) -> list[PlanRun]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(1, window_days))
    runs: list[PlanRun] = []

    for path in sorted(plan_dir.glob("*.json")):
        payload = load_json(path)
        history = payload.get("history") or []
        if not isinstance(history, list) or not history:
            continue
        finished = None
        for event in reversed(history):
            if str(event.get("event_type") or "") == "attempt_finished":
                finished = event
                break
        if not isinstance(finished, dict):
            continue
        ts = parse_timestamp(str(finished.get("timestamp") or ""))
        if ts is None or ts < cutoff:
            continue
        plan_payload = finished.get("plan_payload") or payload.get("plan_payload") or {}
        query = str(plan_payload.get("query") or "")
        class_id, class_label = classify_class(query, class_rules)
        statuses = [row for row in (finished.get("statuses") or []) if isinstance(row, dict)]
        subplans = [row for row in (plan_payload.get("subplans") or []) if isinstance(row, dict)]
        expected_ids = {str(sp.get("subplan_id") or "") for sp in subplans if str(sp.get("subplan_id") or "")}
        base_status_rows = [row for row in statuses if str(row.get("subplan_id") or "") in expected_ids]
        total_subplans = len(expected_ids)
        first_attempt_success = sum(1 for row in base_status_rows if str(row.get("status") or "") in SUCCESS_STATUSES)
        first_attempt_quality_rate = (
            round(first_attempt_success / total_subplans, 3) if total_subplans > 0 else 0.0
        )

        plan_recoveries = [x for x in (plan_payload.get("recoveries") or []) if isinstance(x, dict)]
        split_like_statuses = [
            row
            for row in statuses
            if str(row.get("strategy") or "") == "split_subplan"
            or bool(row.get("retry"))
            or str(row.get("retry_strategy") or "")
        ]
        rescue_count = len(split_like_statuses) + len(plan_recoveries)
        escalation_count = sum(
            1
            for row in statuses
            if str(row.get("status") or "").startswith("deferred")
            or str(row.get("status") or "") == "dropped_family_budget"
            or bool(row.get("escalation_hint"))
        )
        guard_count = sum(
            1
            for row in statuses
            if str(row.get("status") or "") in {"dropped_preflight", "deferred_worker_budget", "deferred_manager_policy"}
            or "no_dispatch" in str((row.get("rollback_contract") or {}).get("strategy") or "")
        )

        state = str(finished.get("state") or "")
        failure_code = int(finished.get("failure_code") or 0)
        success = failure_code == 0 and state in {"succeeded", "partial_success"}
        ranking_version = str((plan_payload.get("provenance") or {}).get("ranking_version") or "")
        failure_signature = _status_failure_signature(statuses)
        plan_id = str(payload.get("plan_id") or path.stem)
        attribution_profile = campaign_profiles.get(plan_id, "normal")
        attribution_primary = _primary_attribution_label(
            success=success,
            rescue_count=rescue_count,
            guard_count=guard_count,
            ranking_version=ranking_version,
            first_attempt_quality_rate=first_attempt_quality_rate,
        )
        runs.append(
            PlanRun(
                plan_id=plan_id,
                timestamp=ts.isoformat(),
                query=query,
                class_id=class_id,
                class_label=class_label,
                ranking_version=ranking_version,
                state=state,
                failure_code=failure_code,
                total_subplans=total_subplans,
                first_attempt_success=first_attempt_success,
                first_attempt_quality_rate=first_attempt_quality_rate,
                rescue_count=rescue_count,
                escalation_count=escalation_count,
                guard_count=guard_count,
                success=success,
                failure_signature=failure_signature,
                attribution_profile=attribution_profile,
                attribution_primary=attribution_primary,
            )
        )
    runs.sort(key=lambda r: r.timestamp, reverse=True)
    return runs


def select_task_set(
    runs: list[PlanRun],
    *,
    min_tasks_per_class: int,
    max_tasks_per_class: int,
) -> tuple[list[PlanRun], dict[str, int]]:
    selected: list[PlanRun] = []
    class_counts: dict[str, int] = defaultdict(int)
    by_class: dict[str, list[PlanRun]] = defaultdict(list)
    for run in runs:
        by_class[run.class_id].append(run)
    for class_id, items in by_class.items():
        if class_id == "unclassified":
            continue
        take = min(max(0, max_tasks_per_class), len(items))
        chosen = items[:take]
        if len(chosen) < max(0, min_tasks_per_class):
            continue
        selected.extend(chosen)
        class_counts[class_id] = len(chosen)
    selected.sort(key=lambda r: r.timestamp, reverse=True)
    return selected, dict(class_counts)


def _safe_rate(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 3)


def summarize_metrics(task_set: list[PlanRun]) -> dict[str, Any]:
    total = len(task_set)
    successes = sum(1 for r in task_set if r.success)
    rescue_runs = sum(1 for r in task_set if r.rescue_count > 0)
    escalation_runs = sum(1 for r in task_set if r.escalation_count > 0)
    first_attempt_sum = sum(r.first_attempt_success for r in task_set)
    first_attempt_total = sum(r.total_subplans for r in task_set)
    failure_signatures = [r.failure_signature for r in task_set if r.failure_signature]
    sig_counter = Counter(failure_signatures)
    recurring_failure_runs = sum(1 for sig in failure_signatures if sig_counter[sig] > 1)
    recurrence_rate = _safe_rate(recurring_failure_runs, len(failure_signatures))
    return {
        "task_count": total,
        "success_count": successes,
        "success_rate": _safe_rate(successes, total),
        "rescue_rate": _safe_rate(rescue_runs, total),
        "escalation_rate": _safe_rate(escalation_runs, total),
        "first_attempt_quality_rate": _safe_rate(first_attempt_sum, first_attempt_total),
        "recurrence_rate": recurrence_rate,
        "recurrence_signatures": [
            {"signature": sig, "count": count}
            for sig, count in sig_counter.most_common(10)
            if count > 1
        ],
    }


def summarize_by_class(task_set: list[PlanRun]) -> list[dict[str, Any]]:
    grouped: dict[str, list[PlanRun]] = defaultdict(list)
    for run in task_set:
        grouped[run.class_id].append(run)
    rows: list[dict[str, Any]] = []
    for class_id, runs in sorted(grouped.items()):
        metrics = summarize_metrics(runs)
        rows.append(
            {
                "class_id": class_id,
                "class_label": runs[0].class_label if runs else class_id,
                **metrics,
            }
        )
    return rows


def summarize_by_profile(task_set: list[PlanRun], configured_profiles: list[str]) -> dict[str, Any]:
    grouped: dict[str, list[PlanRun]] = defaultdict(list)
    for run in task_set:
        grouped[run.attribution_profile].append(run)
    profile_metrics: dict[str, Any] = {}
    for profile in configured_profiles:
        profile_metrics[profile] = summarize_metrics(grouped.get(profile, []))
    for profile, runs in grouped.items():
        if profile not in profile_metrics:
            profile_metrics[profile] = summarize_metrics(runs)

    normal = profile_metrics.get("normal", {})
    mgr_reduced = profile_metrics.get("manager_reduced", {})
    rag_reduced = profile_metrics.get("rag_reduced", {})
    first_only = profile_metrics.get("first_attempt_only", {})
    guard_runs = [r for r in task_set if r.guard_count > 0]
    guard_success = sum(1 for r in guard_runs if r.success)

    attribution_primary = Counter(r.attribution_primary for r in task_set)
    return {
        "profile_metrics": profile_metrics,
        "gain_estimates": {
            "model_first_attempt_signal": first_only.get("first_attempt_quality_rate", 0.0)
            if first_only.get("task_count", 0) > 0
            else normal.get("first_attempt_quality_rate", 0.0),
            "manager_gain_estimate": round(
                normal.get("success_rate", 0.0) - mgr_reduced.get("success_rate", 0.0),
                3,
            )
            if mgr_reduced.get("task_count", 0) > 0
            else None,
            "retrieval_gain_estimate": round(
                normal.get("success_rate", 0.0) - rag_reduced.get("success_rate", 0.0),
                3,
            )
            if rag_reduced.get("task_count", 0) > 0
            else None,
            "guard_policy_effectiveness": _safe_rate(guard_success, len(guard_runs)),
        },
        "attribution_primary_counts": dict(attribution_primary),
    }


def evaluate_pass_fail(metrics: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "success_rate": {
            "value": metrics["success_rate"],
            "target": float(thresholds.get("min_success_rate", 0.0)),
            "direction": "min",
        },
        "rescue_rate": {
            "value": metrics["rescue_rate"],
            "target": float(thresholds.get("max_rescue_rate", 1.0)),
            "direction": "max",
        },
        "escalation_rate": {
            "value": metrics["escalation_rate"],
            "target": float(thresholds.get("max_escalation_rate", 1.0)),
            "direction": "max",
        },
        "recurrence_rate": {
            "value": metrics["recurrence_rate"],
            "target": float(thresholds.get("max_recurrence_rate", 1.0)),
            "direction": "max",
        },
        "first_attempt_quality_rate": {
            "value": metrics["first_attempt_quality_rate"],
            "target": float(thresholds.get("min_first_attempt_quality_rate", 0.0)),
            "direction": "min",
        },
    }
    for item in checks.values():
        if item["direction"] == "min":
            item["pass"] = item["value"] >= item["target"]
        else:
            item["pass"] = item["value"] <= item["target"]
    return {
        "overall_pass": all(bool(item["pass"]) for item in checks.values()),
        "checks": checks,
    }


def to_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Codex 5.1 Replacement Benchmark")
    lines.append("")
    lines.append(f"- generated_at_utc: {summary['generated_at_utc']}")
    lines.append(f"- task_count: {summary['metrics']['task_count']}")
    lines.append(f"- overall_pass: {summary['pass_fail']['overall_pass']}")
    lines.append("")
    lines.append("## Core Metrics")
    for key in ("success_rate", "rescue_rate", "escalation_rate", "recurrence_rate", "first_attempt_quality_rate"):
        lines.append(f"- {key}: {summary['metrics'][key]}")
    lines.append("")
    lines.append("## Pass/Fail Checks")
    for name, item in summary["pass_fail"]["checks"].items():
        lines.append(
            f"- {name}: value={item['value']} target={item['target']} direction={item['direction']} pass={item['pass']}"
        )
    lines.append("")
    lines.append("## Class Metrics")
    for row in summary["class_metrics"]:
        lines.append(
            f"- {row['class_id']}: tasks={row['task_count']} success_rate={row['success_rate']} "
            f"rescue_rate={row['rescue_rate']} escalation_rate={row['escalation_rate']} "
            f"first_attempt_quality_rate={row['first_attempt_quality_rate']}"
        )
    lines.append("")
    lines.append("## Attribution")
    gain = summary["attribution"]["gain_estimates"]
    lines.append(f"- model_first_attempt_signal: {gain['model_first_attempt_signal']}")
    lines.append(f"- manager_gain_estimate: {gain['manager_gain_estimate']}")
    lines.append(f"- retrieval_gain_estimate: {gain['retrieval_gain_estimate']}")
    lines.append(f"- guard_policy_effectiveness: {gain['guard_policy_effectiveness']}")
    for key, value in summary["attribution"]["attribution_primary_counts"].items():
        lines.append(f"- attribution_primary::{key}: {value}")
    lines.append("")
    lines.append("## Recurrence Signatures")
    if not summary["metrics"]["recurrence_signatures"]:
        lines.append("- none")
    else:
        for item in summary["metrics"]["recurrence_signatures"]:
            lines.append(f"- {item['signature']}: {item['count']}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(out_dir: Path, summary: dict[str, Any], markdown: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    (out_dir / "latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "latest.md").write_text(markdown + "\n", encoding="utf-8")
    (out_dir / f"benchmark_{ts}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / f"benchmark_{ts}.md").write_text(markdown + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Codex 5.1 replacement benchmark.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--plan-dir", default=str(DEFAULT_PLAN_DIR))
    parser.add_argument("--campaign-runs", default=str(DEFAULT_CAMPAIGN_RUNS))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json(Path(args.config).resolve())
    window_days = int(config.get("window_days", 30))
    class_rules = [row for row in config.get("class_rules", []) if isinstance(row, dict)]
    task_cfg = config.get("task_set", {}) if isinstance(config.get("task_set"), dict) else {}
    min_tasks = int(task_cfg.get("min_tasks_per_class", 1))
    max_tasks = int(task_cfg.get("max_tasks_per_class", 6))
    profiles = [str(p) for p in config.get("attribution_profiles", []) if str(p)]

    campaign_profiles = _load_campaign_profiles(Path(args.campaign_runs).resolve())
    runs = load_plan_runs(
        plan_dir=Path(args.plan_dir).resolve(),
        class_rules=class_rules,
        window_days=window_days,
        campaign_profiles=campaign_profiles,
    )
    task_set, class_counts = select_task_set(
        runs,
        min_tasks_per_class=min_tasks,
        max_tasks_per_class=max_tasks,
    )
    metrics = summarize_metrics(task_set)
    class_metrics = summarize_by_class(task_set)
    attribution = summarize_by_profile(task_set, profiles)
    pass_fail = evaluate_pass_fail(metrics, config.get("pass_fail", {}))

    summary = {
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_path": str(Path(args.config).resolve()),
        "task_set": {
            "count": len(task_set),
            "class_counts": class_counts,
            "items": [
                {
                    "plan_id": run.plan_id,
                    "timestamp": run.timestamp,
                    "class_id": run.class_id,
                    "query": run.query,
                    "attribution_profile": run.attribution_profile,
                    "attribution_primary": run.attribution_primary,
                }
                for run in task_set
            ],
        },
        "metrics": metrics,
        "class_metrics": class_metrics,
        "attribution": attribution,
        "pass_fail": pass_fail,
    }

    markdown = to_markdown(summary)
    if args.write_report:
        write_outputs(Path(args.out_dir).resolve(), summary, markdown)
    if args.json_only:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
