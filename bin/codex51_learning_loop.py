#!/usr/bin/env python3
"""Operational learning loop from real Codex51 artifacts.

learning-v15 objective:
- capture verbose run-level lessons from real benchmark/campaign/curation/trace artifacts,
- emit prevention candidates that reduce repeated failures,
- publish first-attempt shaping priors by class/family,
- publish execution-acceleration outputs for reuse,
- consume the reusable code library into first-attempt and replay recommendations,
- emit ranked first-attempt decision-support cards that combine weak-class pressure,
  trusted guidance, and reusable code recommendations.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from _datetime_compat import UTC
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = REPO_ROOT / "artifacts" / "codex51" / "benchmark" / "latest.json"
DEFAULT_CAMPAIGN_RUNS = REPO_ROOT / "artifacts" / "codex51" / "campaign" / "runs.jsonl"
DEFAULT_CURATION = REPO_ROOT / "artifacts" / "codex51" / "curation"
DEFAULT_MANIFEST = REPO_ROOT / "config" / "promotion_manifest.json"
DEFAULT_ATTRIBUTION = REPO_ROOT / "artifacts" / "codex51" / "attribution" / "latest.json"
DEFAULT_MANAGER6_TRACES = REPO_ROOT / "artifacts" / "manager6" / "traces.jsonl"
DEFAULT_MANAGER6_PLANS_DIR = REPO_ROOT / "artifacts" / "manager6" / "plans"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "codex51" / "learning"
DEFAULT_EXTERNAL_PATTERNS = REPO_ROOT / "artifacts" / "codex51" / "external_patterns" / "patterns.jsonl"
DEFAULT_EXTERNAL_PRIORS = REPO_ROOT / "artifacts" / "codex51" / "external_patterns" / "best_practice_priors.json"
DEFAULT_TRUSTED_SOURCES = REPO_ROOT / "config" / "trusted_pattern_sources.json"

STOPWORDS = {
    "and",
    "or",
    "the",
    "for",
    "with",
    "from",
    "into",
    "that",
    "this",
    "then",
    "than",
    "when",
    "where",
    "while",
    "over",
    "under",
    "before",
    "after",
    "across",
    "without",
    "within",
    "only",
    "safe",
    "stage",
    "manager",
    "plan",
    "task",
}


@dataclass(frozen=True)
class CampaignRun:
    campaign_run_id: str
    plan_id: str
    task_id: str
    task_title: str
    task_class: str
    lane: str
    timestamp_utc: str
    started_at_utc: str
    success: bool
    in_scope: bool
    dry_run: bool
    return_code: int
    outcome: str
    rescue_count: int
    escalation_count: int
    guard_count: int
    first_attempt_quality_rate: float
    attribution_profile: str
    attribution_primary: str
    ranking_version: str
    command: str
    plan_result: dict[str, Any]


@dataclass(frozen=True)
class PlanArtifact:
    plan_id: str
    query: str
    notes: str
    subplans: list[dict[str, Any]]
    manager_decisions: dict[str, Any]
    stage_reconciliation: dict[str, Any]
    history: list[dict[str, Any]]
    checkpoints: dict[str, dict[str, Any]]
    trace_extra: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    raw = ts[:-1] + "+00:00" if ts.endswith("Z") else ts
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"\s+", " ", text)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_]{3,}", text.lower())
    return [tok for tok in tokens if tok not in STOPWORDS]


def _top_tokens(texts: list[str], *, top_n: int) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(_tokenize(text))
    return [tok for tok, _ in counts.most_common(max(1, top_n))]


def _top_bigrams(texts: list[str], *, top_n: int) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        toks = _tokenize(text)
        for idx in range(len(toks) - 1):
            counts[f"{toks[idx]} {toks[idx + 1]}"] += 1
    return [tok for tok, _ in counts.most_common(max(1, top_n))]


def _prefix(path: str) -> str:
    value = str(path or "").strip().lstrip("./")
    if not value:
        return "unknown"
    bits = value.split("/")
    return f"{bits[0]}/" if len(bits) > 1 else bits[0]


def _load_campaign_runs(path: Path, *, window_days: int) -> list[CampaignRun]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(1, window_days))
    runs: list[CampaignRun] = []
    for row in _read_jsonl(path):
        ts_raw = str(row.get("timestamp_utc") or row.get("started_at_utc") or "")
        ts = _parse_ts(ts_raw)
        if ts is None or ts < cutoff:
            continue
        plan_result = row.get("plan_result") if isinstance(row.get("plan_result"), dict) else {}
        runs.append(
            CampaignRun(
                campaign_run_id=str(row.get("campaign_run_id") or ""),
                plan_id=str(row.get("plan_id") or ""),
                task_id=str(row.get("task_id") or ""),
                task_title=str(row.get("task_title") or ""),
                task_class=str(row.get("task_class") or "unknown"),
                lane=str(row.get("lane") or "unknown"),
                timestamp_utc=str(row.get("timestamp_utc") or ""),
                started_at_utc=str(row.get("started_at_utc") or ""),
                success=bool(row.get("success")),
                in_scope=bool(row.get("in_scope", True)),
                dry_run=bool(row.get("dry_run")),
                return_code=_safe_int(row.get("return_code"), default=0),
                outcome=str(row.get("outcome") or ""),
                rescue_count=_safe_int(row.get("rescue_count")),
                escalation_count=_safe_int(row.get("escalation_count")),
                guard_count=_safe_int(row.get("guard_count")),
                first_attempt_quality_rate=_safe_float(row.get("first_attempt_quality_rate")),
                attribution_profile=str(row.get("attribution_profile") or "normal"),
                attribution_primary=str(row.get("attribution_primary") or "mixed_gain"),
                ranking_version=str(row.get("ranking_version") or ""),
                command=str(row.get("command") or ""),
                plan_result=plan_result,
            )
        )
    runs.sort(key=lambda x: x.timestamp_utc, reverse=True)
    return runs


def _load_curation_rows(curation_dir: Path) -> dict[str, list[dict[str, Any]]]:
    names = {
        "training_examples": "training_examples.jsonl",
        "template_candidates": "template_candidates.jsonl",
        "guard_candidates": "guard_candidates.jsonl",
        "benchmark_wins": "benchmark_wins.jsonl",
        "failures_for_training": "failures_for_training.jsonl",
    }
    return {key: _read_jsonl(curation_dir / filename) for key, filename in names.items()}


def _learning_status_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    versions = manifest.get("subsystem_versions") if isinstance(manifest.get("subsystem_versions"), dict) else {}
    learning = versions.get("learning_training_attribution_loop")
    if isinstance(learning, dict):
        return learning
    return {
        "current_version": "untracked",
        "next_version": "untracked",
        "after_next_version": "untracked",
        "status": "held",
    }


def _extract_benchmark_items(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    task_set = benchmark.get("task_set")
    if isinstance(task_set, dict):
        rows = task_set.get("items")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _class_metrics_from_benchmark(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    rows = benchmark.get("class_metrics")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _load_manager6_trace_index(trace_path: Path, *, window_days: int) -> dict[str, dict[str, Any]]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(1, window_days))
    by_plan: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(trace_path):
        extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
        plan_id = str(extra.get("plan_id") or "")
        if not plan_id:
            continue
        ts_raw = str(row.get("timestamp") or row.get("timestamp_utc") or "")
        ts = _parse_ts(ts_raw)
        if ts is not None and ts < cutoff:
            continue
        if (
            plan_id not in by_plan
            or str(by_plan[plan_id].get("timestamp") or "") < str(row.get("timestamp") or row.get("timestamp_utc") or "")
        ):
            by_plan[plan_id] = row
    return by_plan


def _load_manager6_plan_artifacts(
    plans_dir: Path,
    *,
    plan_ids: set[str],
    trace_index: dict[str, dict[str, Any]],
) -> dict[str, PlanArtifact]:
    out: dict[str, PlanArtifact] = {}
    for plan_id in sorted(plan_ids):
        if not plan_id:
            continue
        plan_path = plans_dir / f"{plan_id}.json"
        payload: dict[str, Any] = {}
        if plan_path.exists():
            try:
                raw = _read_json(plan_path)
            except json.JSONDecodeError:
                raw = {}
            if isinstance(raw, dict):
                payload = raw.get("plan_payload") if isinstance(raw.get("plan_payload"), dict) else {}
                history = raw.get("history") if isinstance(raw.get("history"), list) else []
            else:
                history = []
        else:
            history = []

        query = _normalize_text(payload.get("query"))
        notes = _normalize_text(payload.get("notes"))
        subplans = payload.get("subplans") if isinstance(payload.get("subplans"), list) else []
        manager_decisions = payload.get("manager_decisions") if isinstance(payload.get("manager_decisions"), dict) else {}
        stage_reconciliation = payload.get("stage_reconciliation") if isinstance(payload.get("stage_reconciliation"), dict) else {}

        checkpoint_path = plans_dir / plan_id / "checkpoints.json"
        checkpoints: dict[str, dict[str, Any]] = {}
        if checkpoint_path.exists():
            try:
                cp_raw = _read_json(checkpoint_path)
            except json.JSONDecodeError:
                cp_raw = {}
            cp_subplans = cp_raw.get("subplans") if isinstance(cp_raw.get("subplans"), dict) else {}
            for subplan_id, row in cp_subplans.items():
                if isinstance(row, dict):
                    checkpoints[str(subplan_id)] = row

        trace = trace_index.get(plan_id, {})
        trace_extra = trace.get("extra") if isinstance(trace.get("extra"), dict) else {}
        if not subplans and isinstance(trace_extra.get("subplans"), list):
            subplans = [row for row in trace_extra.get("subplans") if isinstance(row, dict)]
        if not manager_decisions and isinstance(trace_extra.get("manager_decisions"), dict):
            manager_decisions = trace_extra.get("manager_decisions")
        if not stage_reconciliation and isinstance((trace_extra.get("plan_payload") or {}).get("stage_reconciliation"), dict):
            stage_reconciliation = trace_extra["plan_payload"]["stage_reconciliation"]
        if not query and isinstance(trace_extra.get("plan_payload"), dict):
            query = _normalize_text(trace_extra["plan_payload"].get("query"))

        out[plan_id] = PlanArtifact(
            plan_id=plan_id,
            query=query,
            notes=notes,
            subplans=subplans,
            manager_decisions=manager_decisions,
            stage_reconciliation=stage_reconciliation,
            history=[row for row in history if isinstance(row, dict)],
            checkpoints=checkpoints,
            trace_extra=trace_extra,
        )
    return out


def _collect_subplan_rows(plan: PlanArtifact) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if plan.checkpoints:
        rows.extend(row for row in plan.checkpoints.values() if isinstance(row, dict))
    if not rows:
        rows.extend(row for row in plan.subplans if isinstance(row, dict))
    return rows


def _extract_target_paths(subplan_rows: list[dict[str, Any]]) -> list[str]:
    targets: list[str] = []
    for row in subplan_rows:
        for target in row.get("targets") or []:
            value = _normalize_text(target)
            if value:
                targets.append(value)
    seen: set[str] = set()
    unique: list[str] = []
    for target in targets:
        if target in seen:
            continue
        seen.add(target)
        unique.append(target)
    return unique


def _extract_contract_strategies(subplan_rows: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in subplan_rows:
        for contract in row.get("target_contracts") or []:
            if not isinstance(contract, dict):
                continue
            strategy = _normalize_text(contract.get("contract_strategy"))
            if strategy:
                out.append(strategy)
    return out


def _first_failure_event(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in history:
        if str(event.get("state") or "") == "failed":
            return event
    return None


def _history_transitions(history: list[dict[str, Any]]) -> list[str]:
    transitions: list[str] = []
    for event in history:
        et = _normalize_text(event.get("event_type"))
        st = _normalize_text(event.get("state"))
        if et or st:
            transitions.append(f"{et or 'event'}:{st or 'state'}")
    return transitions


def _dominant_weakness(run: CampaignRun, lesson_query: str, *, plan: PlanArtifact) -> tuple[str, dict[str, float]]:
    model = max(0.0, 1.0 - run.first_attempt_quality_rate) * 2.0
    manager = run.rescue_count * 0.8 + run.escalation_count * 0.9
    retrieval = 0.0
    guard = run.guard_count * 1.1

    lower_query = lesson_query.lower()
    if run.task_class == "retrieval_orchestration" or run.attribution_primary == "retrieval_gain":
        retrieval += 1.6
    if any(tok in lower_query for tok in ["retrieval", "rag", "anchor", "search", "cluster"]):
        retrieval += 0.7
    if any(tok in lower_query for tok in ["contract", "literal", "guard"]):
        guard += 0.4

    strategy_rows = plan.manager_decisions.get("strategy_decisions") if isinstance(plan.manager_decisions, dict) else []
    if isinstance(strategy_rows, list):
        for row in strategy_rows:
            if not isinstance(row, dict):
                continue
            reason = str(row.get("reason") or "").lower()
            if any(tok in reason for tok in ["split", "defer", "budget", "fallback", "rescue"]):
                manager += 0.3
            if "learning_priors" in str(row.get("decision_tags") or ""):
                manager += 0.1

    scores = {
        "model_weakness": round(model, 3),
        "manager_weakness": round(manager, 3),
        "retrieval_weakness": round(retrieval, 3),
        "guard_weakness": round(guard, 3),
    }
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if len(ordered) < 2:
        return "mixed", scores
    if ordered[0][1] <= 0.0:
        return "mixed", scores
    if ordered[0][1] - ordered[1][1] < 0.25:
        return "mixed", scores
    return ordered[0][0], scores


def _derive_prevention_patterns(
    run: CampaignRun,
    *,
    dominant_weakness: str,
    target_paths: list[str],
    first_failure: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    signatures: list[str] = [run.task_class, dominant_weakness]
    if run.first_attempt_quality_rate < 0.5:
        signatures.append("low_first_attempt")
    if run.rescue_count > 0:
        signatures.append("rescue_dependency")
    if run.escalation_count > 0:
        signatures.append("escalation_present")
    if run.guard_count > 0:
        signatures.append("guard_triggered")
    if first_failure is not None:
        signatures.append(f"failure_code_{_safe_int(first_failure.get('failure_code'), 0)}")
    if target_paths:
        signatures.append(_prefix(target_paths[0]).replace("/", ""))
    signature = "|".join(signatures)

    actions: list[str] = []
    if dominant_weakness == "model_weakness":
        actions.append("Add class-targeted positive/negative training bundle from this lesson.")
        actions.append("Strengthen first-attempt contract text prior for this task family.")
    elif dominant_weakness == "manager_weakness":
        actions.append("Add manager pre-dispatch split/defer heuristic for this failure signature.")
        actions.append("Raise recurrence-pressure handling before grouped dispatch.")
    elif dominant_weakness == "retrieval_weakness":
        actions.append("Inject retrieval anchor prefixes and demote stale target families for this class.")
        actions.append("Increase conflict/yield prior penalty for this signature.")
    elif dominant_weakness == "guard_weakness":
        actions.append("Add deterministic preflight guard for this signature before dispatch.")
        actions.append("Emit contract-risk warning when this query/target shape appears.")
    else:
        actions.append("Apply combined guard + manager preflight + retrieval shaping for this mixed signature.")
    return signature, actions


def _lesson_object(
    run: CampaignRun,
    *,
    plan: PlanArtifact,
    benchmark_item: dict[str, Any] | None,
    curation_matches: list[dict[str, Any]],
) -> dict[str, Any]:
    subplan_rows = _collect_subplan_rows(plan)
    target_paths = _extract_target_paths(subplan_rows)
    contract_strategies = _extract_contract_strategies(subplan_rows)
    lesson_query = _normalize_text(plan.query or (benchmark_item or {}).get("query") or run.task_title)
    history = plan.history
    first_failure = _first_failure_event(history)
    history_transitions = _history_transitions(history)
    had_failure_then_success = bool(first_failure is not None and run.success)

    dominant, weakness_scores = _dominant_weakness(run, lesson_query, plan=plan)
    signature, prevention_actions = _derive_prevention_patterns(
        run,
        dominant_weakness=dominant,
        target_paths=target_paths,
        first_failure=first_failure,
    )

    rescue_or_fallback: list[str] = []
    if run.rescue_count > 0:
        rescue_or_fallback.append(f"manager_or_family_rescue_count={run.rescue_count}")
    if run.escalation_count > 0:
        rescue_or_fallback.append(f"escalation_count={run.escalation_count}")
    if run.guard_count > 0:
        rescue_or_fallback.append(f"guard_count={run.guard_count}")
    if had_failure_then_success:
        rescue_or_fallback.append("history shows failed attempt followed by successful completion")

    initial_wrong: list[str] = []
    if run.first_attempt_quality_rate < 1.0:
        initial_wrong.append("first attempt did not fully succeed")
    if first_failure is not None:
        initial_wrong.append(
            f"attempt failed in history with failure_code={_safe_int(first_failure.get('failure_code'), 0)}"
        )
    if run.return_code != 0:
        initial_wrong.append(f"non-zero return_code={run.return_code}")
    if run.guard_count > 0:
        initial_wrong.append("guard intervention was required")

    eventually_worked = "success" if run.success else "failed"
    if run.success and run.first_attempt_quality_rate >= 0.85 and not rescue_or_fallback:
        eventually_worked = "clean_first_attempt_success"
    elif run.success and rescue_or_fallback:
        eventually_worked = "success_after_rescue_or_retry"

    contract_risk_score = round(
        (1.0 if run.guard_count > 0 else 0.0)
        + (0.8 if any("literal" in s for s in contract_strategies) else 0.0)
        + (0.5 if any("safe_contract" in run.task_class for _ in [0]) else 0.0),
        3,
    )

    promote = {
        "template": bool(run.success and run.first_attempt_quality_rate >= 0.85 and not rescue_or_fallback),
        "replay_target": bool((not run.success) or run.first_attempt_quality_rate < 0.7),
        "training_example": bool(run.first_attempt_quality_rate < 0.75 or dominant == "model_weakness"),
        "guard_candidate": bool(run.guard_count > 0 or dominant == "guard_weakness"),
        "retrieval_rule_candidate": bool(dominant == "retrieval_weakness"),
        "manager_policy_candidate": bool(dominant == "manager_weakness" or run.rescue_count > 0 or run.escalation_count > 0),
    }

    curation_destinations = sorted(
        {
            str(row.get("curation_destination") or "")
            for row in curation_matches
            if isinstance(row, dict) and str(row.get("curation_destination") or "")
        }
    )

    lesson = {
        "schema_version": "learning_lesson_v12",
        "plan_id": run.plan_id,
        "campaign_run_id": run.campaign_run_id,
        "timestamp_utc": run.timestamp_utc,
        "started_at_utc": run.started_at_utc,
        "task": {
            "task_id": run.task_id,
            "task_title": run.task_title,
            "task_class": run.task_class,
            "lane": run.lane,
            "in_scope": run.in_scope,
            "query": lesson_query,
            "command": run.command,
            "attribution_profile": run.attribution_profile,
            "attribution_primary": run.attribution_primary,
            "ranking_version": run.ranking_version,
        },
        "attempted": {
            "subplan_count": len(subplan_rows),
            "target_count": len(target_paths),
            "target_paths": target_paths,
            "target_prefixes": sorted({_prefix(path) for path in target_paths}),
            "contract_strategies": sorted(set(contract_strategies)),
            "history_transitions": history_transitions,
        },
        "what_initially_went_wrong": initial_wrong,
        "what_eventually_worked": {
            "outcome": eventually_worked,
            "success": run.success,
            "return_code": run.return_code,
            "had_failure_then_success": had_failure_then_success,
            "reconciliation_present": bool(plan.stage_reconciliation),
        },
        "rescue_or_fallback_required": rescue_or_fallback,
        "prevention": {
            "failure_signature": signature,
            "would_have_prevented_issue": prevention_actions,
            "contract_risk_score": contract_risk_score,
        },
        "weakness_classification": {
            "dominant": dominant,
            "scores": weakness_scores,
            "is_mixed": dominant == "mixed",
        },
        "promotion_recommendations": promote,
        "reusable_signals": {
            "curation_destinations": curation_destinations,
            "manager_decision_keys": sorted((plan.manager_decisions or {}).keys()),
            "stage_reconciliation_keys": sorted((plan.stage_reconciliation or {}).keys()),
        },
        "first_attempt_quality": {
            "rate": round(run.first_attempt_quality_rate, 3),
            "rescue_count": run.rescue_count,
            "escalation_count": run.escalation_count,
            "guard_count": run.guard_count,
        },
    }
    return lesson


def _build_lessons(
    *,
    runs: list[CampaignRun],
    plan_index: dict[str, PlanArtifact],
    benchmark_items_by_plan: dict[str, dict[str, Any]],
    curation_rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    curation_by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rows in curation_rows.values():
        for row in rows:
            if not isinstance(row, dict):
                continue
            plan_id = str(row.get("plan_id") or "")
            if plan_id:
                curation_by_plan[plan_id].append(row)

    lessons: list[dict[str, Any]] = []
    for run in runs:
        plan = plan_index.get(run.plan_id)
        if plan is None:
            plan = PlanArtifact(
                plan_id=run.plan_id,
                query="",
                notes="",
                subplans=[],
                manager_decisions={},
                stage_reconciliation={},
                history=[],
                checkpoints={},
                trace_extra={},
            )
        benchmark_item = benchmark_items_by_plan.get(run.plan_id)
        curation_matches = curation_by_plan.get(run.plan_id, [])
        lessons.append(
            _lesson_object(
                run,
                plan=plan,
                benchmark_item=benchmark_item,
                curation_matches=curation_matches,
            )
        )
    lessons.sort(key=lambda row: row.get("timestamp_utc") or "", reverse=True)
    return lessons


def _weak_class_summary(benchmark_classes: list[dict[str, Any]], lessons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lesson in lessons:
        cls = str((((lesson.get("task") or {}).get("task_class")) or "unknown"))
        by_class[cls].append(lesson)

    summary: list[dict[str, Any]] = []
    for row in benchmark_classes:
        class_id = str(row.get("class_id") or "unknown")
        cls_lessons = by_class.get(class_id, [])
        success_rate = _safe_float(row.get("success_rate"), 0.0)
        rescue_rate = _safe_float(row.get("rescue_rate"), 0.0)
        escalation_rate = _safe_float(row.get("escalation_rate"), 0.0)
        recurrence_rate = _safe_float(row.get("recurrence_rate"), 0.0)
        first_attempt = _safe_float(row.get("first_attempt_quality_rate"), 0.0)

        lesson_penalty = 0.0
        if cls_lessons:
            lesson_penalty = sum(
                1.0 - _safe_float(((lesson.get("first_attempt_quality") or {}).get("rate")), 0.0)
                for lesson in cls_lessons
            ) / len(cls_lessons)

        weakness_score = round(
            (1.0 - success_rate) * 3.0
            + rescue_rate * 2.0
            + escalation_rate * 2.0
            + recurrence_rate * 2.5
            + max(0.0, 0.7 - first_attempt) * 3.0
            + lesson_penalty,
            3,
        )

        dominant_counts = Counter(
            str((lesson.get("weakness_classification") or {}).get("dominant") or "mixed")
            for lesson in cls_lessons
        )
        dominant = dominant_counts.most_common(1)[0][0] if dominant_counts else "mixed"

        summary.append(
            {
                "class_id": class_id,
                "class_label": str(row.get("class_label") or class_id),
                "task_count": _safe_int(row.get("task_count"), 0),
                "success_rate": round(success_rate, 3),
                "rescue_rate": round(rescue_rate, 3),
                "escalation_rate": round(escalation_rate, 3),
                "recurrence_rate": round(recurrence_rate, 3),
                "first_attempt_quality_rate": round(first_attempt, 3),
                "weakness_score": weakness_score,
                "dominant_weakness": dominant,
                "lesson_count": len(cls_lessons),
            }
        )
    summary.sort(key=lambda item: item["weakness_score"], reverse=True)
    return summary


def _replay_queue_from_lessons(lessons: list[dict[str, Any]], *, max_items: int) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    seen: set[str] = set()
    for lesson in lessons:
        promote = lesson.get("promotion_recommendations") or {}
        if not bool(promote.get("replay_target")):
            continue
        task = lesson.get("task") or {}
        task_id = str(task.get("task_id") or "")
        if not task_id or task_id in seen:
            continue
        prevention = lesson.get("prevention") or {}
        queue.append(
            {
                "task_id": task_id,
                "task_class": str(task.get("task_class") or "unknown"),
                "source_plan_id": str(lesson.get("plan_id") or ""),
                "reason": str(prevention.get("failure_signature") or "replay_needed"),
                "replay_command": (
                    "python3 bin/local_replacement_campaign.py --config config/local_first_campaign.json "
                    f"run --task-id {task_id} --profile normal --no-dry-run"
                ),
            }
        )
        seen.add(task_id)
        if len(queue) >= max(1, max_items):
            break
    return queue


def _build_prevention_outputs(lessons: list[dict[str, Any]], *, max_items: int) -> dict[str, Any]:
    by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lesson in lessons:
        signature = str(((lesson.get("prevention") or {}).get("failure_signature")) or "")
        if signature:
            by_signature[signature].append(lesson)

    repeated: list[dict[str, Any]] = []
    for signature, rows in by_signature.items():
        if len(rows) < 2:
            continue
        task_classes = sorted({str(((row.get("task") or {}).get("task_class")) or "unknown") for row in rows})
        weaknesses = sorted(
            {str(((row.get("weakness_classification") or {}).get("dominant")) or "mixed") for row in rows}
        )
        plan_ids = [str(row.get("plan_id") or "") for row in rows]
        timestamps = [str(row.get("timestamp_utc") or "") for row in rows]
        actions = []
        for row in rows[:3]:
            actions.extend((row.get("prevention") or {}).get("would_have_prevented_issue") or [])
        dedup_actions = []
        for action in actions:
            if action not in dedup_actions:
                dedup_actions.append(action)
        owner = "mixed"
        if "guard_weakness" in weaknesses and len(weaknesses) == 1:
            owner = "guard"
        elif "manager_weakness" in weaknesses and len(weaknesses) == 1:
            owner = "manager"
        elif "retrieval_weakness" in weaknesses and len(weaknesses) == 1:
            owner = "retrieval"
        elif "model_weakness" in weaknesses and len(weaknesses) == 1:
            owner = "model"

        repeated.append(
            {
                "signature": signature,
                "occurrence_count": len(rows),
                "task_classes": task_classes,
                "dominant_weaknesses": weaknesses,
                "first_seen_utc": min(timestamps) if timestamps else "",
                "last_seen_utc": max(timestamps) if timestamps else "",
                "impacted_plan_ids": plan_ids,
                "recommended_owner": owner,
                "recommended_actions": dedup_actions[:8],
                "known_bad_task_shapes": [
                    {
                        "plan_id": str(row.get("plan_id") or ""),
                        "query": str(((row.get("task") or {}).get("query")) or ""),
                        "target_prefixes": (row.get("attempted") or {}).get("target_prefixes") or [],
                    }
                    for row in rows[:5]
                ],
            }
        )

    repeated.sort(key=lambda row: row.get("occurrence_count", 0), reverse=True)

    contract_risk = sorted(
        (
            {
                "plan_id": str(row.get("plan_id") or ""),
                "task_id": str(((row.get("task") or {}).get("task_id")) or ""),
                "task_class": str(((row.get("task") or {}).get("task_class")) or "unknown"),
                "contract_risk_score": _safe_float(((row.get("prevention") or {}).get("contract_risk_score")), 0.0),
                "warning": "contract-risk warning: tighten literal/guard preflight before dispatch",
            }
            for row in lessons
            if _safe_float(((row.get("prevention") or {}).get("contract_risk_score")), 0.0) >= 1.2
        ),
        key=lambda item: item["contract_risk_score"],
        reverse=True,
    )

    stale_warnings: list[dict[str, Any]] = []
    for row in repeated:
        first_seen = _parse_ts(str(row.get("first_seen_utc") or ""))
        last_seen = _parse_ts(str(row.get("last_seen_utc") or ""))
        if first_seen is None or last_seen is None:
            continue
        if (last_seen - first_seen).total_seconds() >= 6 * 3600:
            stale_warnings.append(
                {
                    "signature": row["signature"],
                    "warning": "stale-pattern warning: signature persists across multiple windows",
                    "occurrence_count": row["occurrence_count"],
                    "first_seen_utc": row["first_seen_utc"],
                    "last_seen_utc": row["last_seen_utc"],
                }
            )

    return {
        "repeated_failure_signatures": repeated[: max(1, max_items)],
        "contract_risk_warnings": contract_risk[: max(1, max_items)],
        "stale_pattern_warnings": stale_warnings[: max(1, max_items)],
    }


def _build_first_attempt_priors(
    lessons: list[dict[str, Any]],
    *,
    class_reuse_recommendations: dict[str, dict[str, Any]],
    max_items: int,
) -> list[dict[str, Any]]:
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lesson in lessons:
        cls = str((((lesson.get("task") or {}).get("task_class")) or "unknown"))
        by_class[cls].append(lesson)

    priors: list[dict[str, Any]] = []
    for cls, rows in by_class.items():
        good = [
            row
            for row in rows
            if bool((row.get("what_eventually_worked") or {}).get("success"))
            and _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 0.0)) >= 0.8
            and not (row.get("rescue_or_fallback_required") or [])
        ]
        bad = [
            row
            for row in rows
            if (not bool((row.get("what_eventually_worked") or {}).get("success")))
            or _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 1.0)) < 0.55
        ]

        good_queries = [str(((row.get("task") or {}).get("query")) or "") for row in good]
        bad_queries = [str(((row.get("task") or {}).get("query")) or "") for row in bad]

        good_targets = [
            prefix
            for row in good
            for prefix in ((row.get("attempted") or {}).get("target_prefixes") or [])
            if prefix
        ]
        good_contracts = [
            strategy
            for row in good
            for strategy in ((row.get("attempted") or {}).get("contract_strategies") or [])
            if strategy
        ]

        strategy_counts: Counter[str] = Counter()
        for row in good:
            for transition in (row.get("attempted") or {}).get("history_transitions") or []:
                if transition:
                    strategy_counts[str(transition)] += 1

        reuse = class_reuse_recommendations.get(cls) or {}
        priors.append(
            {
                "task_class": cls,
                "sample_size": len(rows),
                "good_sample_size": len(good),
                "bad_sample_size": len(bad),
                "recommended_prompt_framing_tokens": _top_tokens(good_queries, top_n=10),
                "recommended_prompt_bigrams": _top_bigrams(good_queries, top_n=8),
                "known_bad_wording_patterns": _top_bigrams(bad_queries, top_n=8),
                "recommended_target_selection_hints": [tok for tok, _ in Counter(good_targets).most_common(6)],
                "recommended_contract_patterns": [tok for tok, _ in Counter(good_contracts).most_common(6)],
                "recommended_decomposition_style": [tok for tok, _ in strategy_counts.most_common(6)],
                "known_good_task_shapes": [
                    {
                        "plan_id": str(row.get("plan_id") or ""),
                        "query": str(((row.get("task") or {}).get("query")) or ""),
                        "target_prefixes": (row.get("attempted") or {}).get("target_prefixes") or [],
                    }
                    for row in good[:3]
                ],
                "known_bad_task_shapes": [
                    {
                        "plan_id": str(row.get("plan_id") or ""),
                        "query": str(((row.get("task") or {}).get("query")) or ""),
                        "target_prefixes": (row.get("attempted") or {}).get("target_prefixes") or [],
                    }
                    for row in bad[:3]
                ],
                "preferred_library_items": reuse.get("preferred_library_items") or [],
                "avoid_library_items": reuse.get("avoid_library_items") or [],
                "trusted_external_suggestions": reuse.get("trusted_external_suggestions") or [],
                "trusted_external_avoid": reuse.get("trusted_external_avoid") or [],
                "recommended_complexity_level": reuse.get("recommended_complexity_level") or "medium",
                "known_good_reuse_patterns": reuse.get("known_good_reuse_patterns") or [],
            }
        )

    priors.sort(key=lambda row: row.get("sample_size", 0), reverse=True)
    return priors[: max(1, max_items)]


def _build_execution_acceleration(
    lessons: list[dict[str, Any]],
    priors: list[dict[str, Any]],
    *,
    class_reuse_recommendations: dict[str, dict[str, Any]],
    max_items: int,
) -> dict[str, Any]:
    template_rows = [row for row in lessons if bool((row.get("promotion_recommendations") or {}).get("template"))]
    template_rows = sorted(
        template_rows,
        key=lambda row: _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 0.0)),
        reverse=True,
    )

    exemplars = sorted(
        lessons,
        key=lambda row: (
            1 if bool((row.get("what_eventually_worked") or {}).get("success")) else 0,
            _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 0.0)),
            -len((row.get("rescue_or_fallback_required") or [])),
        ),
        reverse=True,
    )

    decomposition_counts: Counter[str] = Counter()
    recovery_counts: Counter[str] = Counter()
    anchor_counts: Counter[str] = Counter()
    dispatch_counts: Counter[str] = Counter()

    for row in lessons:
        for transition in (row.get("attempted") or {}).get("history_transitions") or []:
            if transition.startswith("attempt_"):
                decomposition_counts[transition] += 1
        rescue = row.get("rescue_or_fallback_required") or []
        if rescue and bool((row.get("what_eventually_worked") or {}).get("success")):
            for item in rescue:
                recovery_counts[str(item)] += 1
        for prefix in (row.get("attempted") or {}).get("target_prefixes") or []:
            if bool((row.get("what_eventually_worked") or {}).get("success")):
                anchor_counts[str(prefix)] += 1
        cmd = str(((row.get("task") or {}).get("command")) or "")
        if "--profile first_attempt_only" in cmd:
            dispatch_counts["profile:first_attempt_only"] += 1
        if "--profile manager_reduced" in cmd:
            dispatch_counts["profile:manager_reduced"] += 1
        if "--profile rag_reduced" in cmd:
            dispatch_counts["profile:rag_reduced"] += 1
        if "--no-dry-run" in cmd:
            dispatch_counts["dispatch:no_dry_run"] += 1

    class_defaults = [
        {
            "task_class": row.get("task_class"),
            "high_confidence_defaults": {
                "prompt_tokens": row.get("recommended_prompt_framing_tokens") or [],
                "target_hints": row.get("recommended_target_selection_hints") or [],
                "contract_patterns": row.get("recommended_contract_patterns") or [],
            },
        }
        for row in priors
    ]

    reuse_suggestions = [
        {
            "task_class": cls,
            "reuse_first": (rec.get("preferred_library_items") or [])[:4],
            "avoid_first": (rec.get("avoid_library_items") or [])[:4],
            "recommended_complexity_level": rec.get("recommended_complexity_level") or "medium",
        }
        for cls, rec in sorted(class_reuse_recommendations.items())
    ]

    return {
        "top_reusable_templates": [
            {
                "plan_id": str(row.get("plan_id") or ""),
                "task_id": str(((row.get("task") or {}).get("task_id")) or ""),
                "task_class": str(((row.get("task") or {}).get("task_class")) or "unknown"),
                "query": str(((row.get("task") or {}).get("query")) or ""),
            }
            for row in template_rows[: max(1, max_items)]
        ],
        "strong_exemplar_runs": [
            {
                "plan_id": str(row.get("plan_id") or ""),
                "task_id": str(((row.get("task") or {}).get("task_id")) or ""),
                "task_class": str(((row.get("task") or {}).get("task_class")) or "unknown"),
                "first_attempt_quality_rate": _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 0.0)),
                "rescue_or_fallback_required": row.get("rescue_or_fallback_required") or [],
            }
            for row in exemplars[: max(1, max_items)]
        ],
        "high_confidence_task_family_defaults": class_defaults[: max(1, max_items)],
        "reusable_decomposition_patterns": [
            {"pattern": key, "count": count}
            for key, count in decomposition_counts.most_common(max(1, max_items))
        ],
        "reusable_recovery_patterns": [
            {"pattern": key, "count": count}
            for key, count in recovery_counts.most_common(max(1, max_items))
        ],
        "known_effective_code_anchor_strategies": [
            {"target_prefix": key, "count": count}
            for key, count in anchor_counts.most_common(max(1, max_items))
        ],
        "preferred_dispatch_patterns": [
            {"pattern": key, "count": count}
            for key, count in dispatch_counts.most_common(max(1, max_items))
        ],
        "reusable_code_suggestions_by_class": reuse_suggestions[: max(1, max_items)],
    }


def _git_recent_commit_records(*, window_days: int, max_commits: int = 500) -> list[dict[str, Any]]:
    since = (datetime.now(UTC) - timedelta(days=max(1, window_days))).strftime("%Y-%m-%dT%H:%M:%SZ")
    cmd = [
        "git",
        "log",
        f"--since={since}",
        f"-n{max(20, max_commits)}",
        "--name-only",
        "--pretty=format:%H%x1f%cI%x1f%s%x1e",
    ]
    try:
        raw = subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []

    records: list[dict[str, Any]] = []
    for block in raw.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if not lines:
            continue
        header = lines[0].split("\x1f")
        if len(header) < 3:
            continue
        commit_hash, committed_at, subject = header[0], header[1], header[2]
        files = [line.strip() for line in lines[1:] if line.strip()]
        records.append(
            {
                "commit_hash": commit_hash,
                "committed_at": committed_at,
                "subject": subject,
                "files": files,
            }
        )
    return records


def _extract_py_functions(content: str) -> list[dict[str, Any]]:
    lines = content.splitlines()
    starts: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        m = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if m:
            starts.append((idx, m.group(1)))
    out: list[dict[str, Any]] = []
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(lines)
        body_lines = lines[start:end]
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        if not body_lines:
            continue
        out.append(
            {
                "name": name,
                "start_line": start + 1,
                "end_line": start + len(body_lines),
                "line_count": len(body_lines),
                "snippet": "\n".join(body_lines[: min(len(body_lines), 14)]),
            }
        )
    return out


def _extract_sh_functions(content: str) -> list[dict[str, Any]]:
    lines = content.splitlines()
    starts: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{", line.strip())
        if m:
            starts.append((idx, m.group(1)))
    out: list[dict[str, Any]] = []
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(lines)
        body_lines = lines[start:end]
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        if not body_lines:
            continue
        out.append(
            {
                "name": name,
                "start_line": start + 1,
                "end_line": start + len(body_lines),
                "line_count": len(body_lines),
                "snippet": "\n".join(body_lines[: min(len(body_lines), 16)]),
            }
        )
    return out


def _file_dependencies(path: Path, content: str) -> list[str]:
    deps: set[str] = set()
    if path.suffix == ".py":
        for line in content.splitlines():
            line = line.strip()
            m1 = re.match(r"^import\s+([A-Za-z0-9_., ]+)", line)
            m2 = re.match(r"^from\s+([A-Za-z0-9_.]+)\s+import\s+", line)
            if m1:
                for item in m1.group(1).split(","):
                    dep = item.strip().split(" as ")[0].strip()
                    if dep:
                        deps.add(dep)
            elif m2:
                deps.add(m2.group(1).strip())
    elif path.suffix == ".sh":
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("source "):
                deps.add(line.replace("source", "", 1).strip().strip('"'))
            elif line.startswith(". "):
                deps.add(line[2:].strip().strip('"'))
    return sorted(dep for dep in deps if dep)


def _complexity_level(*, kind: str, line_count: int, file_count: int, reuse_hits: int) -> str:
    score = 0
    score += 1 if kind in {"snippet", "template"} else 2
    score += 1 if line_count > 24 else 0
    score += 1 if line_count > 80 else 0
    score += 1 if file_count > 1 else 0
    score += 1 if reuse_hits >= 4 else 0
    if score <= 2:
        return "low"
    if score <= 4:
        return "medium"
    return "high"


def _reuse_confidence(*, success_hits: int, commit_hits: int, positive_hits: int, negative_hits: int) -> float:
    raw = success_hits * 0.9 + commit_hits * 0.5 + positive_hits * 0.8 - negative_hits * 0.6
    return round(max(0.0, min(1.0, raw / 6.0)), 3)


def _build_code_library(
    *,
    lessons: list[dict[str, Any]],
    commit_records: list[dict[str, Any]],
    max_items: int,
) -> dict[str, Any]:
    successful_lessons = [
        row
        for row in lessons
        if bool((row.get("what_eventually_worked") or {}).get("success"))
    ]

    file_to_runs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    file_to_bad_runs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in lessons:
        targets = (row.get("attempted") or {}).get("target_paths") or []
        for path in targets:
            if bool((row.get("what_eventually_worked") or {}).get("success")):
                file_to_runs[str(path)].append(row)
            else:
                file_to_bad_runs[str(path)].append(row)

    commit_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for commit in commit_records:
        for file_path in commit.get("files") or []:
            commit_by_file[str(file_path)].append(commit)

    snippets: list[dict[str, Any]] = []
    helpers: list[dict[str, Any]] = []
    templates: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []
    patterns: list[dict[str, Any]] = []

    # Templates from recurring successful dispatch shapes.
    command_patterns: Counter[str] = Counter()
    command_sources: dict[str, list[str]] = defaultdict(list)
    for row in successful_lessons:
        cmd = str(((row.get("task") or {}).get("command")) or "")
        if not cmd:
            continue
        normalized = re.sub(r"\d{6,}", "<num>", cmd)
        normalized = re.sub(r"campaign-[A-Za-z0-9_-]+", "campaign-<task>", normalized)
        normalized = re.sub(r"--plan-id\s+\S+", "--plan-id <plan>", normalized)
        normalized = re.sub(r"--commit-msg\s+\S+", "--commit-msg <msg>", normalized)
        command_patterns[normalized] += 1
        command_sources[normalized].append(str(row.get("plan_id") or ""))

    for cmd, count in command_patterns.most_common(max(1, max_items)):
        src = command_sources.get(cmd, [])
        templates.append(
            {
                "library_kind": "template",
                "key": f"template:{abs(hash(cmd))}",
                "template_text": cmd,
                "source_runs": src[:10],
                "source_commits": [],
                "reuse_confidence": _reuse_confidence(
                    success_hits=count,
                    commit_hits=0,
                    positive_hits=count,
                    negative_hits=0,
                ),
                "dependencies": [],
                "known_good_use_cases": sorted(
                    {
                        str(((row.get("task") or {}).get("task_class")) or "unknown")
                        for row in successful_lessons
                        if str(((row.get("task") or {}).get("command")) or "") and re.sub(r"\d{6,}", "<num>", str(((row.get("task") or {}).get("command")) or "")) == cmd
                    }
                ),
                "known_bad_use_cases": [],
                "complexity_level": _complexity_level(kind="template", line_count=1, file_count=1, reuse_hits=count),
                "classification": {
                    "family": "dispatch",
                    "class": "command_template",
                    "complexity": _complexity_level(kind="template", line_count=1, file_count=1, reuse_hits=count),
                },
            }
        )

    # File-backed helpers/modules/snippets from successful run targets.
    for file_path, rows in sorted(file_to_runs.items(), key=lambda item: len(item[1]), reverse=True):
        path = (REPO_ROOT / file_path).resolve()
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        line_count = len(content.splitlines())
        deps = _file_dependencies(path, content)
        success_hits = len(rows)
        negative_hits = len(file_to_bad_runs.get(file_path, []))
        commits = commit_by_file.get(file_path, [])
        source_commits = [str(c.get("commit_hash") or "") for c in commits[:12] if c.get("commit_hash")]
        source_runs = [str(r.get("plan_id") or "") for r in rows[:12] if r.get("plan_id")]
        classes_good = sorted({str(((r.get("task") or {}).get("task_class")) or "unknown") for r in rows})
        classes_bad = sorted(
            {
                str(((r.get("task") or {}).get("task_class")) or "unknown")
                for r in file_to_bad_runs.get(file_path, [])
            }
        )

        if path.suffix == ".py":
            funcs = _extract_py_functions(content)
        elif path.suffix == ".sh":
            funcs = _extract_sh_functions(content)
        else:
            funcs = []

        if funcs:
            for fn in funcs[: max(1, min(max_items, 20))]:
                helper_conf = _reuse_confidence(
                    success_hits=success_hits,
                    commit_hits=len(commits),
                    positive_hits=success_hits,
                    negative_hits=negative_hits,
                )
                helper = {
                    "library_kind": "helper",
                    "key": f"helper:{file_path}:{fn['name']}",
                    "name": fn["name"],
                    "path": file_path,
                    "line_span": {"start": fn["start_line"], "end": fn["end_line"]},
                    "snippet": fn["snippet"],
                    "source_runs": source_runs,
                    "source_commits": source_commits,
                    "reuse_confidence": helper_conf,
                    "dependencies": deps,
                    "known_good_use_cases": classes_good,
                    "known_bad_use_cases": classes_bad,
                    "complexity_level": _complexity_level(
                        kind="helper",
                        line_count=fn["line_count"],
                        file_count=1,
                        reuse_hits=success_hits,
                    ),
                    "classification": {
                        "family": _prefix(file_path).replace("/", ""),
                        "class": "function_helper",
                        "complexity": _complexity_level(
                            kind="helper",
                            line_count=fn["line_count"],
                            file_count=1,
                            reuse_hits=success_hits,
                        ),
                    },
                }
                helpers.append(helper)
                snippets.append(
                    {
                        "library_kind": "snippet",
                        "key": f"snippet:{file_path}:{fn['name']}",
                        "path": file_path,
                        "name": fn["name"],
                        "snippet": "\n".join(fn["snippet"].splitlines()[:8]),
                        "source_runs": source_runs[:6],
                        "source_commits": source_commits[:6],
                        "reuse_confidence": round(min(1.0, helper_conf + 0.05), 3),
                        "dependencies": deps,
                        "known_good_use_cases": classes_good,
                        "known_bad_use_cases": classes_bad,
                        "complexity_level": _complexity_level(
                            kind="snippet",
                            line_count=min(8, fn["line_count"]),
                            file_count=1,
                            reuse_hits=success_hits,
                        ),
                        "classification": {
                            "family": _prefix(file_path).replace("/", ""),
                            "class": "code_snippet",
                            "complexity": _complexity_level(
                                kind="snippet",
                                line_count=min(8, fn["line_count"]),
                                file_count=1,
                                reuse_hits=success_hits,
                            ),
                        },
                    }
                )

        module_conf = _reuse_confidence(
            success_hits=success_hits,
            commit_hits=len(commits),
            positive_hits=success_hits + (1 if len(funcs) >= 3 else 0),
            negative_hits=negative_hits,
        )
        modules.append(
            {
                "library_kind": "module",
                "key": f"module:{file_path}",
                "path": file_path,
                "function_count": len(funcs),
                "line_count": line_count,
                "source_runs": source_runs,
                "source_commits": source_commits,
                "reuse_confidence": module_conf,
                "dependencies": deps,
                "known_good_use_cases": classes_good,
                "known_bad_use_cases": classes_bad,
                "complexity_level": _complexity_level(
                    kind="module",
                    line_count=line_count,
                    file_count=1,
                    reuse_hits=success_hits,
                ),
                "classification": {
                    "family": _prefix(file_path).replace("/", ""),
                    "class": "module_pattern",
                    "complexity": _complexity_level(
                        kind="module",
                        line_count=line_count,
                        file_count=1,
                        reuse_hits=success_hits,
                    ),
                },
            }
        )

    # Multi-file patterns from successful lessons + commit co-change.
    combo_counts: Counter[str] = Counter()
    combo_runs: dict[str, list[str]] = defaultdict(list)
    combo_commits: dict[str, list[str]] = defaultdict(list)

    for row in successful_lessons:
        paths = sorted(set((row.get("attempted") or {}).get("target_paths") or []))
        if len(paths) < 2:
            continue
        key = " | ".join(paths)
        combo_counts[key] += 1
        combo_runs[key].append(str(row.get("plan_id") or ""))

    for commit in commit_records:
        files = sorted(set(str(f) for f in (commit.get("files") or []) if str(f).startswith(("bin/", "shell/", "config/", "docs/"))))
        if len(files) < 2:
            continue
        key = " | ".join(files[:4])
        combo_counts[key] += 1
        if commit.get("commit_hash"):
            combo_commits[key].append(str(commit.get("commit_hash")))

    for key, count in combo_counts.most_common(max(1, max_items)):
        paths = key.split(" | ")
        patterns.append(
            {
                "library_kind": "multi_file_pattern",
                "key": f"pattern:{abs(hash(key))}",
                "paths": paths,
                "path_count": len(paths),
                "source_runs": combo_runs.get(key, [])[:12],
                "source_commits": combo_commits.get(key, [])[:12],
                "reuse_confidence": _reuse_confidence(
                    success_hits=len(combo_runs.get(key, [])),
                    commit_hits=len(combo_commits.get(key, [])),
                    positive_hits=count,
                    negative_hits=0,
                ),
                "dependencies": sorted({_prefix(path) for path in paths}),
                "known_good_use_cases": sorted(
                    {
                        str(((row.get("task") or {}).get("task_class")) or "unknown")
                        for row in successful_lessons
                        if set(paths).issubset(set((row.get("attempted") or {}).get("target_paths") or []))
                    }
                ),
                "known_bad_use_cases": [],
                "complexity_level": _complexity_level(
                    kind="multi_file_pattern",
                    line_count=20 * len(paths),
                    file_count=len(paths),
                    reuse_hits=count,
                ),
                "classification": {
                    "family": "cross_target",
                    "class": "multi_file_pattern",
                    "complexity": _complexity_level(
                        kind="multi_file_pattern",
                        line_count=20 * len(paths),
                        file_count=len(paths),
                        reuse_hits=count,
                    ),
                },
            }
        )

    # Promotion candidates snippet -> helper -> template -> module.
    helper_index = {row["key"]: row for row in helpers}
    template_index = {row["key"]: row for row in templates}
    module_index = {row["key"]: row for row in modules}
    promotion_candidates: list[dict[str, Any]] = []
    for row in snippets:
        base = _safe_float(row.get("reuse_confidence"), 0.0)
        if base < 0.55:
            continue
        helper_key = row["key"].replace("snippet:", "helper:")
        target_stage = "helper" if helper_key in helper_index else "template"
        promotion_candidates.append(
            {
                "from_kind": "snippet",
                "to_kind": target_stage,
                "source_key": row["key"],
                "target_key": helper_key if target_stage == "helper" else next(iter(template_index.keys()), ""),
                "reuse_confidence": base,
                "justification": "Repeated success-backed snippet with high reuse confidence.",
            }
        )
    for row in helpers:
        base = _safe_float(row.get("reuse_confidence"), 0.0)
        if base < 0.65:
            continue
        module_key = f"module:{row.get('path')}"
        promotion_candidates.append(
            {
                "from_kind": "helper",
                "to_kind": "module" if module_key in module_index else "template",
                "source_key": row["key"],
                "target_key": module_key if module_key in module_index else next(iter(template_index.keys()), ""),
                "reuse_confidence": base,
                "justification": "Helper appears repeatedly in successful runs and commit history.",
            }
        )

    snippets = sorted(snippets, key=lambda item: _safe_float(item.get("reuse_confidence"), 0.0), reverse=True)[
        : max(1, max_items)
    ]
    helpers = sorted(helpers, key=lambda item: _safe_float(item.get("reuse_confidence"), 0.0), reverse=True)[
        : max(1, max_items)
    ]
    templates = sorted(templates, key=lambda item: _safe_float(item.get("reuse_confidence"), 0.0), reverse=True)[
        : max(1, max_items)
    ]
    modules = sorted(modules, key=lambda item: _safe_float(item.get("reuse_confidence"), 0.0), reverse=True)[
        : max(1, max_items)
    ]
    patterns = sorted(patterns, key=lambda item: _safe_float(item.get("reuse_confidence"), 0.0), reverse=True)[
        : max(1, max_items)
    ]

    recommended_reuse_targets: list[dict[str, Any]] = []
    for row in modules[:3] + helpers[:3] + patterns[:3]:
        recommended_reuse_targets.append(
            {
                "library_kind": row.get("library_kind"),
                "key": row.get("key"),
                "reuse_confidence": row.get("reuse_confidence"),
                "recommended_for_next_runs": row.get("known_good_use_cases") or [],
            }
        )

    return {
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_scope": {
            "successful_lessons": len(successful_lessons),
            "commit_records": len(commit_records),
        },
        "summary": {
            "snippets": len(snippets),
            "helpers": len(helpers),
            "templates": len(templates),
            "modules": len(modules),
            "patterns": len(patterns),
            "promotion_candidates": len(promotion_candidates),
        },
        "promotion_candidates": promotion_candidates[: max(1, max_items)],
        "complexity_progression": {
            "low": sum(
                1
                for row in (snippets + helpers + templates + modules + patterns)
                if str(row.get("complexity_level")) == "low"
            ),
            "medium": sum(
                1
                for row in (snippets + helpers + templates + modules + patterns)
                if str(row.get("complexity_level")) == "medium"
            ),
            "high": sum(
                1
                for row in (snippets + helpers + templates + modules + patterns)
                if str(row.get("complexity_level")) == "high"
            ),
        },
        "recommended_reuse_targets": recommended_reuse_targets[: max(1, max_items)],
        "snippets": snippets,
        "helpers": helpers,
        "templates": templates,
        "modules": modules,
        "patterns": patterns,
    }


def _build_library_class_recommendations(
    *,
    code_library: dict[str, Any],
    external_patterns: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    max_items: int,
) -> dict[str, dict[str, Any]]:
    classes = sorted(
        {
            str(((row.get("task") or {}).get("task_class")) or "unknown")
            for row in lessons
            if isinstance(row, dict)
        }
    )
    if not classes:
        return {}

    all_items: list[dict[str, Any]] = []
    for key in ("helpers", "templates", "modules", "patterns", "snippets"):
        rows = code_library.get(key)
        if isinstance(rows, list):
            all_items.extend(row for row in rows if isinstance(row, dict))
    for row in external_patterns:
        if not isinstance(row, dict):
            continue
        all_items.append(
            {
                "key": str(row.get("key") or f"trusted:{row.get('source_name')}:{row.get('source_path')}:{row.get('name')}"),
                "library_kind": str(row.get("pattern_type") or "snippet"),
                "reuse_confidence": _safe_float(row.get("reuse_confidence"), 0.0),
                "complexity_level": str(row.get("complexity_level") or "medium"),
                "dependencies": row.get("dependencies") or [],
                "known_good_use_cases": row.get("known_good_use_cases") or row.get("task_class_hints") or [],
                "known_bad_use_cases": row.get("known_bad_use_cases") or [],
                "trusted_external_reference": True,
                "source_name": row.get("source_name"),
                "source_repo": row.get("source_repo"),
                "source_path": row.get("source_path"),
                "source_revision": row.get("source_revision"),
                "direct_reuse_allowed": bool(row.get("direct_reuse_allowed", True)),
            }
        )

    def _mode_complexity(rows: list[dict[str, Any]]) -> str:
        counts = Counter(str(row.get("complexity_level") or "medium") for row in rows)
        if not counts:
            return "medium"
        return counts.most_common(1)[0][0]

    recommendations: dict[str, dict[str, Any]] = {}
    for cls in classes:
        good_items = [
            row
            for row in all_items
            if cls in [str(x) for x in (row.get("known_good_use_cases") or [])]
            and bool(row.get("direct_reuse_allowed", True))
        ]
        bad_items = [
            row
            for row in all_items
            if cls in [str(x) for x in (row.get("known_bad_use_cases") or [])]
            and cls not in [str(x) for x in (row.get("known_good_use_cases") or [])]
        ]
        good_items.sort(key=lambda row: _safe_float(row.get("reuse_confidence"), 0.0), reverse=True)
        bad_items.sort(key=lambda row: _safe_float(row.get("reuse_confidence"), 0.0), reverse=True)
        preferred: list[dict[str, Any]] = []
        for row in good_items[: max(1, max_items)]:
            preferred.append(
                {
                    "key": str(row.get("key") or ""),
                    "library_kind": str(row.get("library_kind") or "unknown"),
                    "reuse_confidence": _safe_float(row.get("reuse_confidence"), 0.0),
                    "complexity_level": str(row.get("complexity_level") or "medium"),
                    "dependency_hints": (row.get("dependencies") or [])[:4],
                    "trusted_external_reference": bool(row.get("trusted_external_reference")),
                    "source_name": str(row.get("source_name") or ""),
                    "source_repo": str(row.get("source_repo") or ""),
                    "source_path": str(row.get("source_path") or ""),
                    "source_revision": str(row.get("source_revision") or ""),
                }
            )
        avoid: list[dict[str, Any]] = []
        preferred_keys = {str(item.get("key") or "") for item in preferred}
        for row in bad_items[: max(1, max_items * 2)]:
            if str(row.get("key") or "") in preferred_keys:
                continue
            avoid.append(
                {
                    "key": str(row.get("key") or ""),
                    "library_kind": str(row.get("library_kind") or "unknown"),
                    "reason": "known_bad_use_case_for_class",
                    "reuse_confidence": _safe_float(row.get("reuse_confidence"), 0.0),
                }
            )
            if len(avoid) >= max(1, max_items):
                break

        trusted_from_good = [
            {
                "key": str(row.get("key") or ""),
                "library_kind": str(row.get("library_kind") or "unknown"),
                "reuse_confidence": _safe_float(row.get("reuse_confidence"), 0.0),
                "source_name": str(row.get("source_name") or ""),
                "source_repo": str(row.get("source_repo") or ""),
                "source_path": str(row.get("source_path") or ""),
                "source_revision": str(row.get("source_revision") or ""),
                "trusted_external_reference": True,
            }
            for row in good_items
            if bool(row.get("trusted_external_reference"))
        ][: max(1, max_items)]

        recommendations[cls] = {
            "preferred_library_items": preferred,
            "avoid_library_items": avoid,
            "trusted_external_suggestions": trusted_from_good,
            "trusted_external_avoid": [
                item
                for item in avoid
                if "trusted:" in str(item.get("key") or "")
            ][: max(1, max_items)],
            "recommended_complexity_level": _mode_complexity(good_items),
            "known_good_reuse_patterns": [
                {
                    "key": str(row.get("key") or ""),
                    "library_kind": str(row.get("library_kind") or "unknown"),
                }
                for row in good_items
                if str(row.get("library_kind") or "") in {"template", "module", "multi_file_pattern"}
            ][: max(1, max_items)],
        }
    return recommendations


def _build_reuse_recommendation_outputs(
    *,
    weak_classes: list[dict[str, Any]],
    replay_queue: list[dict[str, Any]],
    class_reuse: dict[str, dict[str, Any]],
    max_items: int,
) -> dict[str, Any]:
    by_class: list[dict[str, Any]] = []
    for cls, rec in sorted(class_reuse.items()):
        by_class.append(
            {
                "task_class": cls,
                "preferred_library_items": rec.get("preferred_library_items") or [],
                "known_good_patterns_first": rec.get("known_good_reuse_patterns") or [],
                "avoid_items": rec.get("avoid_library_items") or [],
                "trusted_external_suggestions": rec.get("trusted_external_suggestions") or [],
                "trusted_external_avoid": rec.get("trusted_external_avoid") or [],
                "recommended_complexity_level": rec.get("recommended_complexity_level") or "medium",
            }
        )

    weak_class_targets: list[dict[str, Any]] = []
    for row in weak_classes[: max(1, max_items)]:
        cls = str(row.get("class_id") or "unknown")
        weak_class_targets.append(
            {
                "task_class": cls,
                "weakness_score": _safe_float(row.get("weakness_score"), 0.0),
                "dominant_weakness": str(row.get("dominant_weakness") or "mixed"),
                "recommended_reuse": (class_reuse.get(cls) or {}).get("preferred_library_items") or [],
                "avoid_reuse": (class_reuse.get(cls) or {}).get("avoid_library_items") or [],
                "trusted_external_suggestions": (class_reuse.get(cls) or {}).get("trusted_external_suggestions") or [],
                "recommended_complexity_level": (class_reuse.get(cls) or {}).get("recommended_complexity_level") or "medium",
            }
        )

    replay_suggestions: list[dict[str, Any]] = []
    for row in replay_queue[: max(1, max_items)]:
        cls = str(row.get("task_class") or "unknown")
        replay_suggestions.append(
            {
                "task_id": str(row.get("task_id") or ""),
                "task_class": cls,
                "reuse_first": (class_reuse.get(cls) or {}).get("preferred_library_items") or [],
                "avoid_first": (class_reuse.get(cls) or {}).get("avoid_library_items") or [],
                "trusted_external_suggestions": (class_reuse.get(cls) or {}).get("trusted_external_suggestions") or [],
                "recommended_complexity_level": (class_reuse.get(cls) or {}).get("recommended_complexity_level") or "medium",
            }
        )

    return {
        "by_task_class": by_class[: max(1, max_items)],
        "weak_class_reuse_rankings": weak_class_targets[: max(1, max_items)],
        "replay_reuse_suggestions": replay_suggestions[: max(1, max_items)],
    }


def _build_first_attempt_decision_support(
    *,
    weak_classes: list[dict[str, Any]],
    first_attempt_priors: list[dict[str, Any]],
    prevention_outputs: dict[str, Any],
    reuse_recommendations: dict[str, Any],
    trusted_decision_support: dict[str, Any],
    max_items: int,
) -> dict[str, Any]:
    weak_by_class = {str(row.get("class_id") or "unknown"): row for row in weak_classes if isinstance(row, dict)}
    priors_by_class = {
        str(row.get("task_class") or "unknown"): row for row in first_attempt_priors if isinstance(row, dict)
    }
    reuse_by_class = {
        str(row.get("task_class") or "unknown"): row
        for row in ((reuse_recommendations.get("by_task_class") or []) if isinstance(reuse_recommendations, dict) else [])
        if isinstance(row, dict)
    }
    trusted_by_class = {
        str(row.get("task_class") or "unknown"): row
        for row in ((trusted_decision_support.get("by_task_class") or []) if isinstance(trusted_decision_support, dict) else [])
        if isinstance(row, dict)
    }

    repeated = (
        prevention_outputs.get("repeated_failure_signatures")
        if isinstance(prevention_outputs.get("repeated_failure_signatures"), list)
        else []
    )
    contract_risk = (
        prevention_outputs.get("contract_risk_warnings")
        if isinstance(prevention_outputs.get("contract_risk_warnings"), list)
        else []
    )
    failure_count_by_class: Counter[str] = Counter()
    contract_risk_by_class: Counter[str] = Counter()
    for row in repeated:
        if not isinstance(row, dict):
            continue
        signature = str(row.get("signature") or "")
        class_hint = signature.split("|", 1)[0].strip() if "|" in signature else ""
        if class_hint:
            failure_count_by_class[class_hint] += _safe_int(row.get("occurrence_count"), 1)
    for row in contract_risk:
        if not isinstance(row, dict):
            continue
        signature = str(row.get("signature") or "")
        class_hint = signature.split("|", 1)[0].strip() if "|" in signature else ""
        if class_hint:
            contract_risk_by_class[class_hint] += 1

    classes = sorted(
        set(weak_by_class.keys())
        | set(priors_by_class.keys())
        | set(reuse_by_class.keys())
        | set(trusted_by_class.keys())
    )
    cards: list[dict[str, Any]] = []
    for cls in classes:
        weak = weak_by_class.get(cls) or {}
        prior = priors_by_class.get(cls) or {}
        reuse = reuse_by_class.get(cls) or {}
        trusted = trusted_by_class.get(cls) or {}

        bad_sample = _safe_int(prior.get("bad_sample_size"), 0)
        sample_size = max(1, _safe_int(prior.get("sample_size"), 0))
        bad_ratio = bad_sample / sample_size
        weakness_score = _safe_float(weak.get("weakness_score"), 0.0)
        failure_count = _safe_int(failure_count_by_class.get(cls), 0)
        contract_risk_count = _safe_int(contract_risk_by_class.get(cls), 0)

        priority_score = round(
            (weakness_score * 2.0)
            + (bad_ratio * 1.5)
            + (min(5, failure_count) * 0.35)
            + (min(4, contract_risk_count) * 0.25),
            3,
        )

        use_first = {
            "library_items": (prior.get("preferred_library_items") or [])[: max(1, max_items)],
            "trusted_patterns": (trusted.get("use_first_trusted_patterns") or [])[: max(1, max_items)],
            "library_plus_trusted_combinations": (
                trusted.get("recommended_library_plus_trusted_combinations") or []
            )[: max(1, max_items)],
        }
        avoid_first = {
            "library_items": (prior.get("avoid_library_items") or [])[: max(1, max_items)],
            "trusted_patterns": (trusted.get("avoid_trusted_patterns") or [])[: max(1, max_items)],
            "known_bad_wording_patterns": (prior.get("known_bad_wording_patterns") or [])[: max(1, max_items)],
        }
        recommended_complexity = (
            str(trusted.get("preferred_complexity_level") or "")
            or str(reuse.get("recommended_complexity_level") or "")
            or str(prior.get("recommended_complexity_level") or "medium")
        )
        prompt_defaults = {
            "prompt_tokens": (prior.get("recommended_prompt_framing_tokens") or [])[: max(1, max_items)],
            "prompt_bigrams": (prior.get("recommended_prompt_bigrams") or [])[: max(1, max_items)],
            "target_selection_hints": (prior.get("recommended_target_selection_hints") or [])[: max(1, max_items)],
            "contract_patterns": (prior.get("recommended_contract_patterns") or [])[: max(1, max_items)],
            "decomposition_style": (prior.get("recommended_decomposition_style") or [])[: max(1, max_items)],
        }
        evidence = {
            "sample_size": sample_size,
            "good_sample_size": _safe_int(prior.get("good_sample_size"), 0),
            "bad_sample_size": bad_sample,
            "weakness_score": weakness_score,
            "dominant_weakness": str(weak.get("dominant_weakness") or "mixed"),
            "repeated_failure_count": failure_count,
            "contract_risk_warning_count": contract_risk_count,
            "source_plan_ids": [
                str(row.get("plan_id") or "")
                for row in ((prior.get("known_good_task_shapes") or []) if isinstance(prior.get("known_good_task_shapes"), list) else [])
                if isinstance(row, dict) and str(row.get("plan_id") or "")
            ][: max(1, max_items)],
        }

        cards.append(
            {
                "task_class": cls,
                "priority_score": priority_score,
                "recommended_complexity_level": recommended_complexity,
                "use_first": use_first,
                "avoid_first": avoid_first,
                "prompt_contract_defaults": prompt_defaults,
                "evidence": evidence,
            }
        )

    cards.sort(key=lambda row: (_safe_float(row.get("priority_score"), 0.0), row.get("task_class") or ""), reverse=True)
    return {
        "by_task_class": cards[: max(1, max_items)],
        "highest_priority_class": (cards[0].get("task_class") if cards else "unknown"),
    }


def _trusted_external_summary(
    *,
    external_patterns: list[dict[str, Any]],
    external_priors: dict[str, Any],
    max_items: int,
) -> dict[str, Any]:
    by_source = Counter(str(row.get("source_name") or "unknown") for row in external_patterns)
    by_type = Counter(str(row.get("pattern_type") or "snippet") for row in external_patterns)
    top = sorted(
        external_patterns,
        key=lambda row: _safe_float(row.get("reuse_confidence"), 0.0),
        reverse=True,
    )
    return {
        "pattern_count": len(external_patterns),
        "by_source": dict(by_source),
        "by_pattern_type": dict(by_type),
        "top_trusted_patterns": [
            {
                "source_name": str(row.get("source_name") or ""),
                "pattern_type": str(row.get("pattern_type") or "snippet"),
                "source_path": str(row.get("source_path") or ""),
                "name": str(row.get("name") or ""),
                "reuse_confidence": _safe_float(row.get("reuse_confidence"), 0.0),
                "task_class_hints": row.get("task_class_hints") or row.get("known_good_use_cases") or [],
                "direct_reuse_allowed": bool(row.get("direct_reuse_allowed", True)),
                "adaptation_required": bool(row.get("adaptation_required", True)),
            }
            for row in top[: max(1, max_items)]
        ],
        "best_practice_priors": external_priors,
    }


def _task_class_to_prior_families(task_class: str) -> list[str]:
    mapping = {
        "safe_contracts": ["shell_safety_patterns", "typed_schema_patterns"],
        "resumable_checkpointed": ["shell_safety_patterns", "testing_patterns"],
        "retrieval_orchestration": ["browser_operator_patterns", "python_helper_patterns"],
        "multi_file_orchestration": ["browser_operator_patterns", "testing_patterns", "python_helper_patterns"],
        "bounded_architecture": ["typed_schema_patterns", "python_helper_patterns"],
    }
    return mapping.get(task_class, ["python_helper_patterns", "typed_schema_patterns"])


def _build_trusted_decision_support(
    *,
    external_patterns: list[dict[str, Any]],
    external_priors: dict[str, Any],
    trusted_sources_registry: dict[str, Any],
    class_reuse: dict[str, dict[str, Any]],
    max_items: int,
) -> dict[str, Any]:
    priors_families = (
        external_priors.get("families")
        if isinstance(external_priors.get("families"), dict)
        else {}
    )
    registry_sources = (
        trusted_sources_registry.get("sources")
        if isinstance(trusted_sources_registry.get("sources"), list)
        else []
    )

    by_task_class: list[dict[str, Any]] = []
    for cls in sorted(class_reuse.keys()):
        family_names = _task_class_to_prior_families(cls)
        trusted_candidates = [
            row
            for row in external_patterns
            if isinstance(row, dict) and cls in [str(x) for x in (row.get("task_class_hints") or [])]
        ]
        trusted_candidates.sort(key=lambda row: _safe_float(row.get("reuse_confidence"), 0.0), reverse=True)

        use_first: list[dict[str, Any]] = []
        seen = set()
        for row in trusted_candidates:
            key = str(
                row.get("key")
                or f"trusted:{row.get('source_name')}:{row.get('source_path')}:{row.get('name')}"
            )
            if not key or key in seen:
                continue
            seen.add(key)
            use_first.append(
                {
                    "key": key,
                    "source_name": str(row.get("source_name") or ""),
                    "source_repo": str(row.get("source_repo") or ""),
                    "source_path": str(row.get("source_path") or ""),
                    "pattern_type": str(row.get("pattern_type") or "snippet"),
                    "reuse_confidence": _safe_float(row.get("reuse_confidence"), 0.0),
                    "adaptation_required": bool(row.get("adaptation_required", True)),
                    "direct_reuse_allowed": bool(row.get("direct_reuse_allowed", True)),
                }
            )
            if len(use_first) >= max(1, max_items):
                break

        avoid: list[dict[str, Any]] = []
        for source in registry_sources:
            if not isinstance(source, dict):
                continue
            if cls not in [str(x) for x in (source.get("task_class_hints") or [])]:
                continue
            for rule in source.get("disallowed_direct_reuse_cases") or []:
                avoid.append(
                    {
                        "source_name": str(source.get("source_name") or ""),
                        "source_repo": str(source.get("upstream_repo") or ""),
                        "reason": str(rule),
                        "avoid_type": "disallowed_direct_reuse_case",
                    }
                )

        for family in family_names:
            fam = priors_families.get(family) if isinstance(priors_families, dict) else None
            anti = (
                fam.get("anti_patterns")
                if isinstance(fam, dict) and isinstance(fam.get("anti_patterns"), list)
                else []
            )
            for item in anti:
                if not isinstance(item, dict):
                    continue
                avoid.append(
                    {
                        "source_name": str(item.get("source_name") or ""),
                        "source_repo": str(item.get("source_repo") or ""),
                        "reason": str(item.get("guidance") or item.get("name") or "trusted_anti_pattern"),
                        "avoid_type": "best_practice_anti_pattern",
                    }
                )

        dedup_avoid: list[dict[str, Any]] = []
        seen_avoid = set()
        for row in avoid:
            sig = (row.get("source_name"), row.get("reason"), row.get("avoid_type"))
            if sig in seen_avoid:
                continue
            seen_avoid.add(sig)
            dedup_avoid.append(row)
            if len(dedup_avoid) >= max(1, max_items):
                break

        preferred_library = (class_reuse.get(cls) or {}).get("preferred_library_items") or []
        combinations: list[dict[str, Any]] = []
        for lrow in preferred_library[:3]:
            for trow in use_first[:3]:
                combinations.append(
                    {
                        "task_class": cls,
                        "library_key": str(lrow.get("key") or ""),
                        "library_kind": str(lrow.get("library_kind") or "unknown"),
                        "trusted_key": str(trow.get("key") or ""),
                        "trusted_source": str(trow.get("source_name") or ""),
                        "combo_intent": "use_local_library_skeleton_with_trusted_external_shape",
                    }
                )
                if len(combinations) >= max(1, max_items):
                    break
            if len(combinations) >= max(1, max_items):
                break

        preferred_complexity = (
            str((class_reuse.get(cls) or {}).get("recommended_complexity_level") or "")
            or "medium"
        )
        by_task_class.append(
            {
                "task_class": cls,
                "prior_families": family_names,
                "use_first_trusted_patterns": use_first,
                "avoid_trusted_patterns": dedup_avoid,
                "preferred_complexity_level": preferred_complexity,
                "recommended_library_plus_trusted_combinations": combinations,
            }
        )

    return {"by_task_class": by_task_class}


def _candidate_splits_from_lessons(lessons: list[dict[str, Any]], *, max_items: int) -> dict[str, list[dict[str, Any]]]:
    def _pick(flag: str) -> list[dict[str, Any]]:
        rows = [row for row in lessons if bool((row.get("promotion_recommendations") or {}).get(flag))]
        rows.sort(
            key=lambda row: (
                0 if bool((row.get("what_eventually_worked") or {}).get("success")) else 1,
                _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 0.0)),
            )
        )
        out: list[dict[str, Any]] = []
        for row in rows[: max(1, max_items)]:
            out.append(
                {
                    "plan_id": str(row.get("plan_id") or ""),
                    "task_id": str(((row.get("task") or {}).get("task_id")) or ""),
                    "task_class": str(((row.get("task") or {}).get("task_class")) or "unknown"),
                    "first_attempt_quality_rate": _safe_float(((row.get("first_attempt_quality") or {}).get("rate"), 0.0)),
                    "reason": str(((row.get("prevention") or {}).get("failure_signature")) or ""),
                }
            )
        return out

    return {
        "guard_rule_candidates": _pick("guard_candidate"),
        "manager_rule_candidates": _pick("manager_policy_candidate"),
        "retrieval_rule_candidates": _pick("retrieval_rule_candidate"),
        "training_example_candidates": _pick("training_example"),
        "template_promotion_candidates": _pick("template"),
    }


def _model_vs_wrapper_summary(weak_classes: list[dict[str, Any]], attribution: dict[str, Any]) -> dict[str, Any]:
    model_dominant = [row["class_id"] for row in weak_classes if row.get("dominant_weakness") == "model_weakness"]
    wrapper_dominant = [
        row["class_id"]
        for row in weak_classes
        if row.get("dominant_weakness") in {"manager_weakness", "retrieval_weakness", "guard_weakness"}
    ]
    mixed = [row["class_id"] for row in weak_classes if row.get("dominant_weakness") == "mixed"]

    campaign_agg = attribution.get("campaign_aggregate") if isinstance(attribution.get("campaign_aggregate"), dict) else {}
    bucket_counts = (
        campaign_agg.get("attribution_bucket_counts")
        if isinstance(campaign_agg.get("attribution_bucket_counts"), dict)
        else {}
    )
    local_with_assist = int(bucket_counts.get("local_with_manager_rescue", 0)) + int(
        bucket_counts.get("local_with_rag_assist", 0)
    )
    codex_or_manual = int(bucket_counts.get("codex_or_manual_primary", 0))

    if len(model_dominant) > len(wrapper_dominant) + 1:
        dominant = "model_weakness"
    elif len(wrapper_dominant) > len(model_dominant) + 1:
        dominant = "wrapper_weakness"
    elif codex_or_manual > local_with_assist:
        dominant = "wrapper_weakness"
    else:
        dominant = "mixed"

    return {
        "dominant_gap": dominant,
        "model_dominant_classes": model_dominant,
        "wrapper_dominant_classes": wrapper_dominant,
        "mixed_classes": mixed,
        "campaign_bucket_snapshot": {
            "local_with_assist": local_with_assist,
            "codex_or_manual_primary": codex_or_manual,
            "mixed_or_shared": int(bucket_counts.get("mixed_or_shared", 0)),
        },
    }


def _next_step_recommendations(
    *,
    weak_classes: list[dict[str, Any]],
    replay_queue: list[dict[str, Any]],
    prevention: dict[str, Any],
    model_wrapper: dict[str, Any],
) -> list[str]:
    recs: list[str] = []
    if weak_classes:
        top = weak_classes[0]
        recs.append(
            f"Replay weakest class first: {top['class_id']} (weakness_score={top['weakness_score']}, dominant={top['dominant_weakness']})."
        )
    if replay_queue:
        recs.append(f"Execute blocker-first replay task: {replay_queue[0]['task_id']} ({replay_queue[0]['reason']}).")

    repeated = prevention.get("repeated_failure_signatures") or []
    if repeated:
        first = repeated[0]
        recs.append(
            f"Install prevention owner={first['recommended_owner']} for signature {first['signature']} (count={first['occurrence_count']})."
        )

    contract_risk = prevention.get("contract_risk_warnings") or []
    if contract_risk:
        recs.append("Add pre-dispatch contract-risk warning and guard candidate for highest-risk lesson.")

    if model_wrapper.get("dominant_gap") == "model_weakness":
        recs.append("Prioritize first-attempt priors + training-example promotion before broad wrapper changes.")
    elif model_wrapper.get("dominant_gap") == "wrapper_weakness":
        recs.append("Prioritize guard/manager/retrieval policy updates before adding more training data.")

    if not recs:
        recs.append("No high-pressure weak class detected; run next harder first_attempt_only mixed-family slice.")
    return recs


def _local_first_share(runs: list[CampaignRun]) -> float:
    if not runs:
        return 0.0
    local_success = sum(
        1
        for run in runs
        if run.success and run.rescue_count == 0 and run.escalation_count == 0 and run.guard_count == 0
    )
    return round(local_success / len(runs), 3)


def _attribution_mix(runs: list[CampaignRun]) -> dict[str, int]:
    return dict(Counter(run.attribution_primary for run in runs))


def _report_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    learning = report.get("learning_subsystem") or {}
    lines.append("# Codex51 Learning Loop")
    lines.append("")
    lines.append(f"- generated_at_utc: {report.get('generated_at_utc')}")
    lines.append(f"- learning_current_version: {learning.get('current_version', 'untracked')}")
    lines.append(f"- learning_status: {learning.get('status', 'held')}")
    lines.append(f"- campaign_window_runs: {report.get('campaign_window_runs', 0)}")
    lines.append(f"- local_first_share_window: {report.get('local_first_share_window', 0.0)}")
    lines.append("")

    lines.append("## Verbose Lesson Capture")
    lessons = report.get("lessons") or []
    lines.append(f"- lessons_captured: {len(lessons)}")
    for row in lessons[:5]:
        task = row.get("task") or {}
        lines.append(
            f"- {task.get('task_id', 'unknown')} ({task.get('task_class', 'unknown')}): "
            f"dominant={((row.get('weakness_classification') or {}).get('dominant', 'mixed'))} "
            f"first_attempt={((row.get('first_attempt_quality') or {}).get('rate', 0.0))} "
            f"outcome={((row.get('what_eventually_worked') or {}).get('outcome', 'unknown'))}"
        )
    lines.append("")

    lines.append("## Future-Error Prevention")
    prevention = report.get("prevention_outputs") or {}
    lines.append(
        f"- repeated_failure_signatures: {len(prevention.get('repeated_failure_signatures') or [])}"
    )
    lines.append(f"- contract_risk_warnings: {len(prevention.get('contract_risk_warnings') or [])}")
    lines.append(f"- stale_pattern_warnings: {len(prevention.get('stale_pattern_warnings') or [])}")
    for row in (prevention.get("repeated_failure_signatures") or [])[:4]:
        lines.append(
            f"- signature={row['signature']} count={row['occurrence_count']} owner={row['recommended_owner']}"
        )
    lines.append("")

    lines.append("## First-Attempt Priors")
    priors = report.get("first_attempt_priors") or []
    lines.append(f"- priors_by_class: {len(priors)}")
    for row in priors[:4]:
        lines.append(
            f"- {row['task_class']}: good={row['good_sample_size']} bad={row['bad_sample_size']} "
            f"tokens={', '.join(row.get('recommended_prompt_framing_tokens') or []) or 'none'}"
        )
    lines.append("")

    lines.append("## Execution Acceleration")
    accel = report.get("execution_acceleration") or {}
    lines.append(f"- top_reusable_templates: {len(accel.get('top_reusable_templates') or [])}")
    lines.append(f"- strong_exemplar_runs: {len(accel.get('strong_exemplar_runs') or [])}")
    lines.append(
        f"- reusable_decomposition_patterns: {len(accel.get('reusable_decomposition_patterns') or [])}"
    )
    lines.append(f"- reusable_recovery_patterns: {len(accel.get('reusable_recovery_patterns') or [])}")
    lines.append("")

    lines.append("## Reuse Recommendations")
    reuse = report.get("reuse_recommendations") or {}
    lines.append(f"- by_task_class: {len(reuse.get('by_task_class') or [])}")
    lines.append(f"- weak_class_reuse_rankings: {len(reuse.get('weak_class_reuse_rankings') or [])}")
    lines.append(f"- replay_reuse_suggestions: {len(reuse.get('replay_reuse_suggestions') or [])}")
    for row in (reuse.get("by_task_class") or [])[:4]:
        lines.append(
            f"- {row.get('task_class')}: preferred={len(row.get('preferred_library_items') or [])} "
            f"avoid={len(row.get('avoid_items') or [])} complexity={row.get('recommended_complexity_level')}"
        )
    lines.append("")

    lines.append("## Reusable Code Library")
    clib = report.get("code_library") or {}
    csum = clib.get("summary") if isinstance(clib.get("summary"), dict) else {}
    lines.append(f"- snippets: {csum.get('snippets', 0)}")
    lines.append(f"- helpers: {csum.get('helpers', 0)}")
    lines.append(f"- templates: {csum.get('templates', 0)}")
    lines.append(f"- modules: {csum.get('modules', 0)}")
    lines.append(f"- patterns: {csum.get('patterns', 0)}")
    lines.append(f"- promotion_candidates: {csum.get('promotion_candidates', 0)}")
    for row in (clib.get("recommended_reuse_targets") or [])[:4]:
        lines.append(
            f"- reuse target {row.get('library_kind')}::{row.get('key')} conf={row.get('reuse_confidence')}"
        )
    lines.append("")

    lines.append("## Trusted External Patterns")
    ext = report.get("trusted_external_patterns") or {}
    lines.append(f"- pattern_count: {ext.get('pattern_count', 0)}")
    lines.append(f"- by_source: {ext.get('by_source', {})}")
    lines.append(f"- by_pattern_type: {ext.get('by_pattern_type', {})}")
    for row in (ext.get("top_trusted_patterns") or [])[:4]:
        lines.append(
            f"- {row.get('source_name')}::{row.get('pattern_type')}::{row.get('name')} "
            f"path={row.get('source_path')} conf={row.get('reuse_confidence')}"
        )
    lines.append("")

    lines.append("## Trusted Decision Support")
    tds = report.get("trusted_decision_support") or {}
    lines.append(f"- by_task_class: {len(tds.get('by_task_class') or [])}")
    for row in (tds.get("by_task_class") or [])[:4]:
        lines.append(
            f"- {row.get('task_class')}: use_first={len(row.get('use_first_trusted_patterns') or [])} "
            f"avoid={len(row.get('avoid_trusted_patterns') or [])} "
            f"complexity={row.get('preferred_complexity_level')}"
        )
    lines.append("")

    lines.append("## First-Attempt Decision Support")
    ds = report.get("first_attempt_decision_support") or {}
    lines.append(f"- by_task_class: {len(ds.get('by_task_class') or [])}")
    lines.append(f"- highest_priority_class: {ds.get('highest_priority_class', 'unknown')}")
    for row in (ds.get("by_task_class") or [])[:4]:
        use_first = row.get("use_first") or {}
        avoid_first = row.get("avoid_first") or {}
        evidence = row.get("evidence") or {}
        lines.append(
            f"- {row.get('task_class')}: priority={row.get('priority_score')} "
            f"complexity={row.get('recommended_complexity_level')} "
            f"use={len(use_first.get('library_items') or []) + len(use_first.get('trusted_patterns') or [])} "
            f"avoid={len(avoid_first.get('library_items') or []) + len(avoid_first.get('trusted_patterns') or [])} "
            f"failures={evidence.get('repeated_failure_count', 0)}"
        )
    lines.append("")

    lines.append("## Weak Classes")
    for row in (report.get("weak_class_summary") or [])[:6]:
        lines.append(
            f"- {row['class_id']}: weakness_score={row['weakness_score']} "
            f"first_attempt_quality_rate={row['first_attempt_quality_rate']} dominant={row['dominant_weakness']}"
        )
    lines.append("")

    lines.append("## Prioritized Replay Queue")
    queue = report.get("prioritized_replay_queue") or []
    if not queue:
        lines.append("- none")
    else:
        for row in queue[:8]:
            lines.append(f"- {row['task_id']} ({row['task_class']}): {row['reason']}")
    lines.append("")

    lines.append("## Model Vs Wrapper")
    mvsw = report.get("model_vs_wrapper_summary") or {}
    lines.append(f"- dominant_gap: {mvsw.get('dominant_gap', 'mixed')}")
    lines.append(f"- model_dominant_classes: {', '.join(mvsw.get('model_dominant_classes') or []) or 'none'}")
    lines.append(
        f"- wrapper_dominant_classes: {', '.join(mvsw.get('wrapper_dominant_classes') or []) or 'none'}"
    )
    lines.append("")

    lines.append("## Next Recommended Targets")
    for item in report.get("next_recommended_targets") or []:
        lines.append(f"- {item}")
    lines.append("")

    return "\n".join(lines)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def build_learning_report(
    *,
    benchmark: dict[str, Any],
    runs: list[CampaignRun],
    curation_rows: dict[str, list[dict[str, Any]]],
    manifest: dict[str, Any],
    attribution: dict[str, Any],
    plan_index: dict[str, PlanArtifact],
    commit_records: list[dict[str, Any]],
    external_patterns: list[dict[str, Any]],
    external_priors: dict[str, Any],
    trusted_sources_registry: dict[str, Any],
    max_replay: int,
    max_candidates: int,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    metrics = benchmark.get("metrics") if isinstance(benchmark.get("metrics"), dict) else {}
    benchmark_classes = _class_metrics_from_benchmark(benchmark)
    benchmark_items = _extract_benchmark_items(benchmark)
    benchmark_items_by_plan = {
        str(row.get("plan_id") or ""): row
        for row in benchmark_items
        if isinstance(row, dict) and str(row.get("plan_id") or "")
    }

    lessons = _build_lessons(
        runs=runs,
        plan_index=plan_index,
        benchmark_items_by_plan=benchmark_items_by_plan,
        curation_rows=curation_rows,
    )
    weak_classes = _weak_class_summary(benchmark_classes, lessons)
    replay_queue = _replay_queue_from_lessons(lessons, max_items=max_replay)
    candidate_splits = _candidate_splits_from_lessons(lessons, max_items=max_candidates)
    prevention = _build_prevention_outputs(lessons, max_items=max_candidates)
    code_library = _build_code_library(
        lessons=lessons,
        commit_records=commit_records,
        max_items=max_candidates,
    )
    class_reuse_recommendations = _build_library_class_recommendations(
        code_library=code_library,
        external_patterns=external_patterns,
        lessons=lessons,
        max_items=max_candidates,
    )
    first_attempt_priors = _build_first_attempt_priors(
        lessons,
        class_reuse_recommendations=class_reuse_recommendations,
        max_items=max_candidates,
    )
    acceleration = _build_execution_acceleration(
        lessons,
        first_attempt_priors,
        class_reuse_recommendations=class_reuse_recommendations,
        max_items=max_candidates,
    )
    reuse_recommendations = _build_reuse_recommendation_outputs(
        weak_classes=weak_classes,
        replay_queue=replay_queue,
        class_reuse=class_reuse_recommendations,
        max_items=max_candidates,
    )
    trusted_external = _trusted_external_summary(
        external_patterns=external_patterns,
        external_priors=external_priors,
        max_items=max_candidates,
    )
    trusted_decision_support = _build_trusted_decision_support(
        external_patterns=external_patterns,
        external_priors=external_priors,
        trusted_sources_registry=trusted_sources_registry,
        class_reuse=class_reuse_recommendations,
        max_items=max_candidates,
    )
    first_attempt_decision_support = _build_first_attempt_decision_support(
        weak_classes=weak_classes,
        first_attempt_priors=first_attempt_priors,
        prevention_outputs=prevention,
        reuse_recommendations=reuse_recommendations,
        trusted_decision_support=trusted_decision_support,
        max_items=max_candidates,
    )
    model_wrapper = _model_vs_wrapper_summary(weak_classes, attribution)
    recommendations = _next_step_recommendations(
        weak_classes=weak_classes,
        replay_queue=replay_queue,
        prevention=prevention,
        model_wrapper=model_wrapper,
    )

    learning_version = _learning_status_from_manifest(manifest)
    curation_counts = {key: len(rows) for key, rows in curation_rows.items()}

    report = {
        "schema_version": "learning_report_v15",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "learning_subsystem": learning_version,
        "benchmark_metrics": {
            "success_rate": _safe_float(metrics.get("success_rate")),
            "rescue_rate": _safe_float(metrics.get("rescue_rate")),
            "escalation_rate": _safe_float(metrics.get("escalation_rate")),
            "recurrence_rate": _safe_float(metrics.get("recurrence_rate")),
            "first_attempt_quality_rate": _safe_float(metrics.get("first_attempt_quality_rate")),
        },
        "campaign_window_runs": len(runs),
        "local_first_share_window": _local_first_share(runs),
        "attribution_mix": _attribution_mix(runs),
        "class_metrics": weak_classes,
        "weak_class_summary": weak_classes,
        "weak_class_targets": weak_classes,
        "replay_queue": replay_queue,
        "prioritized_replay_queue": replay_queue,
        "candidate_splits": candidate_splits,
        "lessons": lessons,
        "prevention_outputs": prevention,
        "first_attempt_priors": first_attempt_priors,
        "execution_acceleration": acceleration,
        "reuse_recommendations": reuse_recommendations,
        "trusted_external_patterns": trusted_external,
        "trusted_decision_support": trusted_decision_support,
        "first_attempt_decision_support": first_attempt_decision_support,
        "code_library": {
            "generated_at_utc": code_library.get("generated_at_utc"),
            "summary": code_library.get("summary"),
            "complexity_progression": code_library.get("complexity_progression"),
            "promotion_candidates": code_library.get("promotion_candidates"),
            "recommended_reuse_targets": code_library.get("recommended_reuse_targets"),
            "consumption_by_task_class": class_reuse_recommendations,
            "trusted_external_pattern_count": trusted_external.get("pattern_count", 0),
            "trusted_external_sources": trusted_external.get("by_source", {}),
        },
        "model_vs_wrapper_summary": model_wrapper,
        "curation_counts": curation_counts,
        "next_recommended_targets": recommendations,
        "source_artifacts": {
            "benchmark": str(DEFAULT_BENCHMARK),
            "campaign_runs": str(DEFAULT_CAMPAIGN_RUNS),
            "curation_dir": str(DEFAULT_CURATION),
            "attribution": str(DEFAULT_ATTRIBUTION),
            "manager6_traces": str(DEFAULT_MANAGER6_TRACES),
            "manager6_plans_dir": str(DEFAULT_MANAGER6_PLANS_DIR),
            "external_patterns": str(DEFAULT_EXTERNAL_PATTERNS),
            "external_priors": str(DEFAULT_EXTERNAL_PRIORS),
            "trusted_sources_registry": str(DEFAULT_TRUSTED_SOURCES),
        },
    }

    jsonl_outputs = {
        "lessons": lessons,
        "prevention_candidates": prevention.get("repeated_failure_signatures") or [],
        "first_attempt_priors": first_attempt_priors,
        "execution_acceleration": [acceleration],
        "reuse_recommendations": reuse_recommendations.get("by_task_class") or [],
        "weak_class_targets": weak_classes,
        "code_library_snippets": code_library.get("snippets") or [],
        "code_library_helpers": code_library.get("helpers") or [],
        "code_library_templates": code_library.get("templates") or [],
        "code_library_modules": code_library.get("modules") or [],
        "code_library_patterns": code_library.get("patterns") or [],
        "trusted_external_patterns": external_patterns,
        "trusted_decision_support": trusted_decision_support.get("by_task_class") or [],
        "first_attempt_decision_support": first_attempt_decision_support.get("by_task_class") or [],
    }
    return report, jsonl_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run learning-v15 loop from Codex51 artifacts.")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--campaign-runs", default=str(DEFAULT_CAMPAIGN_RUNS))
    parser.add_argument("--curation-dir", default=str(DEFAULT_CURATION))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--attribution", default=str(DEFAULT_ATTRIBUTION))
    parser.add_argument("--manager6-traces", default=str(DEFAULT_MANAGER6_TRACES))
    parser.add_argument("--manager6-plans-dir", default=str(DEFAULT_MANAGER6_PLANS_DIR))
    parser.add_argument("--external-patterns", default=str(DEFAULT_EXTERNAL_PATTERNS))
    parser.add_argument("--external-priors", default=str(DEFAULT_EXTERNAL_PRIORS))
    parser.add_argument("--trusted-sources", default=str(DEFAULT_TRUSTED_SOURCES))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--max-replay", type=int, default=8)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_path = Path(args.benchmark).resolve()
    campaign_runs_path = Path(args.campaign_runs).resolve()
    curation_dir = Path(args.curation_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    attribution_path = Path(args.attribution).resolve()
    manager6_traces_path = Path(args.manager6_traces).resolve()
    manager6_plans_dir = Path(args.manager6_plans_dir).resolve()
    external_patterns_path = Path(args.external_patterns).resolve()
    external_priors_path = Path(args.external_priors).resolve()
    trusted_sources_path = Path(args.trusted_sources).resolve()

    for required_path, label in [
        (benchmark_path, "benchmark"),
        (campaign_runs_path, "campaign runs"),
        (curation_dir, "curation dir"),
        (manifest_path, "manifest"),
        (attribution_path, "attribution"),
    ]:
        if not required_path.exists():
            print(f"missing {label}: {required_path}")
            return 2

    benchmark = _read_json(benchmark_path)
    manifest = _read_json(manifest_path)
    attribution = _read_json(attribution_path)
    external_patterns = _read_jsonl(external_patterns_path)
    external_priors = _load_optional_json(external_priors_path)
    trusted_sources_registry = _load_optional_json(trusted_sources_path)
    runs = _load_campaign_runs(campaign_runs_path, window_days=max(1, args.window_days))
    curation_rows = _load_curation_rows(curation_dir)

    trace_index = _load_manager6_trace_index(manager6_traces_path, window_days=max(1, args.window_days))
    commit_records = _git_recent_commit_records(window_days=max(1, args.window_days))
    plan_ids = {run.plan_id for run in runs if run.plan_id}
    plan_index = _load_manager6_plan_artifacts(manager6_plans_dir, plan_ids=plan_ids, trace_index=trace_index)

    report, jsonl_outputs = build_learning_report(
        benchmark=benchmark,
        runs=runs,
        curation_rows=curation_rows,
        manifest=manifest,
        attribution=attribution,
        plan_index=plan_index,
        commit_records=commit_records,
        external_patterns=external_patterns,
        external_priors=external_priors,
        trusted_sources_registry=trusted_sources_registry,
        max_replay=max(1, args.max_replay),
        max_candidates=max(1, args.max_candidates),
    )

    if args.write_report:
        out_dir = Path(args.out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        (out_dir / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out_dir / "latest.md").write_text(_report_markdown(report) + "\n", encoding="utf-8")
        (out_dir / f"learning_{ts}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        _write_jsonl(out_dir / "lessons.jsonl", jsonl_outputs["lessons"])
        _write_jsonl(out_dir / "prevention_candidates.jsonl", jsonl_outputs["prevention_candidates"])
        _write_jsonl(out_dir / "first_attempt_priors.jsonl", jsonl_outputs["first_attempt_priors"])
        _write_jsonl(out_dir / "execution_acceleration.jsonl", jsonl_outputs["execution_acceleration"])
        _write_jsonl(out_dir / "reuse_recommendations.jsonl", jsonl_outputs["reuse_recommendations"])
        _write_jsonl(out_dir / "weak_class_targets.jsonl", jsonl_outputs["weak_class_targets"])
        _write_jsonl(out_dir / "trusted_external_patterns.jsonl", jsonl_outputs["trusted_external_patterns"])
        _write_jsonl(out_dir / "trusted_decision_support.jsonl", jsonl_outputs["trusted_decision_support"])
        _write_jsonl(out_dir / "first_attempt_decision_support.jsonl", jsonl_outputs["first_attempt_decision_support"])

        code_library_dir = out_dir / "code_library"
        code_library_dir.mkdir(parents=True, exist_ok=True)
        code_library_payload = report.get("code_library") if isinstance(report.get("code_library"), dict) else {}
        code_library_payload = {
            **code_library_payload,
            "snippets": jsonl_outputs.get("code_library_snippets") or [],
            "helpers": jsonl_outputs.get("code_library_helpers") or [],
            "templates": jsonl_outputs.get("code_library_templates") or [],
            "modules": jsonl_outputs.get("code_library_modules") or [],
            "patterns": jsonl_outputs.get("code_library_patterns") or [],
        }
        (code_library_dir / "latest.json").write_text(
            json.dumps(code_library_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        _write_jsonl(code_library_dir / "snippets.jsonl", jsonl_outputs["code_library_snippets"])
        _write_jsonl(code_library_dir / "helpers.jsonl", jsonl_outputs["code_library_helpers"])
        _write_jsonl(code_library_dir / "templates.jsonl", jsonl_outputs["code_library_templates"])
        _write_jsonl(code_library_dir / "modules.jsonl", jsonl_outputs["code_library_modules"])
        _write_jsonl(code_library_dir / "patterns.jsonl", jsonl_outputs["code_library_patterns"])

    if args.json_only:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_report_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
