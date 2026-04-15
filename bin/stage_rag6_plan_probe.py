#!/usr/bin/env python3
"""Stage RAG-6 planning helper for Stage-7 multi-plan orchestration."""

from __future__ import annotations

import argparse  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op
import collections
import datetime as dt
import itertools
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"
LOG_DIR = REPO_ROOT / "artifacts" / "stage_rag6"
LOG_FILE = LOG_DIR / "usage.jsonl"
MANAGER_PLAN_DIR = REPO_ROOT / "artifacts" / "manager6" / "plans"


def append_log(entry: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _family_key(path: str) -> str:
    name = Path(path).stem.lower()
    for sep in ("_", "-"):
        if sep in name:
            return name.split(sep, 1)[0]
    return name


def _path_tokens(path: str) -> set[str]:
    stem = Path(path).stem.lower()
    raw = [p for p in stem.replace("-", "_").split("_") if p]
    tokens: set[str] = set(raw)
    if "/" in path:
        for part in Path(path).parts:
            part = part.lower()
            if part and part not in {"bin", "docs", "shell"}:
                tokens.add(part)
    return {t for t in tokens if t and len(t) > 1}


def _link_score(candidate: dict[str, Any], primary_path: str) -> float:
    reason = candidate.get("selection_reason", {}) or {}
    related = {str(p) for p in reason.get("related_paths", []) if p}
    if primary_path in related:
        return 2.0
    companion_of = set(reason.get("companion_of", []) or [])
    if primary_path in companion_of:
        return 1.5
    return float(reason.get("companion_link_strength") or 0.0)


def _risk_bucket(confidence: int) -> str:
    if confidence >= 8:
        return "low"
    if confidence >= 5:
        return "medium"
    return "high"


def _status_bucket(status: str) -> str:
    value = (status or "").strip().lower()
    if not value:
        return "other"
    if value in {"success", "resumed_skip_completed"}:
        return "success"
    if value == "failure":
        return "failure"
    if value.startswith("deferred"):
        return "deferred"
    if value.startswith("dropped"):
        return "dropped"
    if "escalat" in value:
        return "escalated"
    return "other"


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 3)


def _parse_iso(ts: str | None) -> dt.datetime | None:
    if not ts:
        return None
    value = ts.strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except ValueError:
        return None


def _new_feedback_counter() -> dict[str, int]:
    return {
        "samples": 0,
        "successes": 0,
        "failures": 0,
        "deferred": 0,
        "dropped": 0,
        "escalated": 0,
    }


def _counter_with_rates(counter: dict[str, int]) -> dict[str, Any]:
    samples = int(counter.get("samples", 0))
    return {
        **counter,
        "success_rate": _rate(int(counter.get("successes", 0)), samples),
        "failure_rate": _rate(int(counter.get("failures", 0)), samples),
        "defer_rate": _rate(int(counter.get("deferred", 0)), samples),
        "drop_rate": _rate(int(counter.get("dropped", 0)), samples),
        "escalation_rate": _rate(int(counter.get("escalated", 0)), samples),
    }


def load_execution_feedback(*, window_days: int, sample_limit: int) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=max(1, window_days))
    family_counters: dict[str, dict[str, int]] = collections.defaultdict(_new_feedback_counter)
    path_counters: dict[str, dict[str, int]] = collections.defaultdict(_new_feedback_counter)
    family_pair_counters: dict[str, dict[str, int]] = collections.defaultdict(_new_feedback_counter)
    processed_files = 0

    plan_paths = sorted(MANAGER_PLAN_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for plan_path in plan_paths:
        if processed_files >= max(1, sample_limit):
            break
        try:
            payload = json.loads(plan_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        history = payload.get("history") or []
        finished = None
        for event in reversed(history):
            if (event.get("event_type") or "") == "attempt_finished":
                finished = event
                break
        if not isinstance(finished, dict):
            continue
        ts = _parse_iso(finished.get("timestamp"))
        if ts and ts < cutoff:
            continue
        statuses = finished.get("statuses") or []
        if not isinstance(statuses, list) or not statuses:
            continue
        plan_payload = finished.get("plan_payload") or payload.get("plan_payload") or {}
        subplans = plan_payload.get("subplans") or []
        subplan_targets: dict[str, tuple[list[str], list[str]]] = {}
        for subplan in subplans:
            if not isinstance(subplan, dict):
                continue
            sid = str(subplan.get("subplan_id") or "")
            if not sid:
                continue
            target_meta = subplan.get("target_meta") or []
            paths: list[str] = []
            families: list[str] = []
            for item in target_meta:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("path") or "")
                family = str(item.get("family") or _family_key(path))
                if path:
                    paths.append(path)
                if family:
                    families.append(family)
            if not paths:
                paths = [str(p) for p in (subplan.get("targets") or []) if p]
                families = [_family_key(p) for p in paths]
            subplan_targets[sid] = (sorted(set(paths)), sorted(set(families)))

        for status_row in statuses:
            if not isinstance(status_row, dict):
                continue
            sid = str(status_row.get("subplan_id") or "")
            if sid not in subplan_targets:
                continue
            bucket = _status_bucket(str(status_row.get("status") or ""))
            if bucket == "other":
                continue
            paths, families = subplan_targets[sid]
            for path in paths:
                ctr = path_counters[path]
                ctr["samples"] += 1
                if bucket == "success":
                    ctr["successes"] += 1
                elif bucket == "failure":
                    ctr["failures"] += 1
                elif bucket == "deferred":
                    ctr["deferred"] += 1
                elif bucket == "dropped":
                    ctr["dropped"] += 1
                elif bucket == "escalated":
                    ctr["escalated"] += 1
            for family in families:
                ctr = family_counters[family]
                ctr["samples"] += 1
                if bucket == "success":
                    ctr["successes"] += 1
                elif bucket == "failure":
                    ctr["failures"] += 1
                elif bucket == "deferred":
                    ctr["deferred"] += 1
                elif bucket == "dropped":
                    ctr["dropped"] += 1
                elif bucket == "escalated":
                    ctr["escalated"] += 1
            if len(families) >= 2:
                for pair in itertools.combinations(sorted(set(families)), 2):
                    pair_key = "|".join(pair)
                    ctr = family_pair_counters[pair_key]
                    ctr["samples"] += 1
                    if bucket == "success":
                        ctr["successes"] += 1
                    elif bucket == "failure":
                        ctr["failures"] += 1
                    elif bucket == "deferred":
                        ctr["deferred"] += 1
                    elif bucket == "dropped":
                        ctr["dropped"] += 1
                    elif bucket == "escalated":
                        ctr["escalated"] += 1
        processed_files += 1

    family_summary = {k: _counter_with_rates(v) for k, v in family_counters.items() if v.get("samples", 0) > 0}
    path_summary = {k: _counter_with_rates(v) for k, v in path_counters.items() if v.get("samples", 0) > 0}
    family_pair_summary = {
        k: _counter_with_rates(v) for k, v in family_pair_counters.items() if v.get("samples", 0) > 0
    }
    return {
        "window_days": max(1, window_days),
        "sample_limit": max(1, sample_limit),
        "processed_plan_files": processed_files,
        "families": family_summary,
        "paths": path_summary,
        "family_pairs": family_pair_summary,
    }


def _feedback_signal(feedback: dict[str, Any]) -> float:
    samples = int(feedback.get("samples", 0))
    if samples <= 0:
        return 0.0
    success = float(feedback.get("success_rate") or 0.0)
    failure = float(feedback.get("failure_rate") or 0.0)
    deferred = float(feedback.get("defer_rate") or 0.0)
    dropped = float(feedback.get("drop_rate") or 0.0)
    escalated = float(feedback.get("escalation_rate") or 0.0)
    return round((success * 3.2) - (failure * 4.4) - (deferred * 2.0) - (dropped * 1.6) - (escalated * 2.4), 3)


def _target_effective_rank(target: dict[str, Any], feedback: dict[str, Any]) -> float:
    path = str(target.get("path") or "")
    rank = float(target.get("rank_score") or 0.0)
    conf = float(target.get("confidence") or 0.0)
    path_feedback = ((feedback.get("paths") or {}).get(path) or {})
    signal = _feedback_signal(path_feedback)
    sample_weight = min(1.0, int(path_feedback.get("samples", 0)) / 5.0)
    return round(rank + (conf * 0.12) + (signal * sample_weight), 4)


def _family_pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def _pair_feedback_signal(feedback: dict[str, Any]) -> float:
    samples = int(feedback.get("samples", 0))
    if samples <= 0:
        return 0.0
    success = float(feedback.get("success_rate") or 0.0)
    failure = float(feedback.get("failure_rate") or 0.0)
    deferred = float(feedback.get("defer_rate") or 0.0)
    dropped = float(feedback.get("drop_rate") or 0.0)
    escalated = float(feedback.get("escalation_rate") or 0.0)
    return round((success * 3.0) - (failure * 4.8) - (deferred * 2.4) - (dropped * 1.8) - (escalated * 2.8), 3)


def _subplan_conflict_meta(cluster: list[dict[str, Any]]) -> tuple[float, list[str]]:
    signals: list[str] = []
    if len(cluster) <= 1:
        return 0.0, signals
    conflict = 0.0
    seen_families: dict[str, int] = {}
    seen_dirs: dict[str, int] = {}
    token_sets = [_path_tokens(str(item.get("path") or "")) for item in cluster]
    for idx, item in enumerate(cluster):
        path = str(item.get("path") or "")
        family = _family_key(path)
        parent = str(Path(path).parent)
        if family:
            seen_families[family] = seen_families.get(family, 0) + 1
        if parent:
            seen_dirs[parent] = seen_dirs.get(parent, 0) + 1
        for jdx in range(idx + 1, len(cluster)):
            overlap = token_sets[idx] & token_sets[jdx]
            if overlap:
                weight = min(1.5, 0.3 * len(overlap))
                conflict += weight
                signals.append(f"token_overlap:{','.join(sorted(list(overlap)[:3]))}")
    repeated_families = [k for k, v in seen_families.items() if v > 1]
    if repeated_families:
        conflict += 0.4 * len(repeated_families)
        signals.append(f"family_repeat:{','.join(sorted(repeated_families)[:3])}")
    repeated_dirs = [k for k, v in seen_dirs.items() if v > 1]
    if repeated_dirs:
        conflict += 0.25 * len(repeated_dirs)
        signals.append(f"dir_repeat:{','.join(sorted(repeated_dirs)[:2])}")
    return round(conflict, 3), signals[:6]


def run_rag4(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(STAGE_RAG4_PLAN),
        "--plan-id",
        f"{args.plan_id}-rag4",
        "--top",
        str(args.top),
        "--window",
        str(args.window),
        "--preview-lines",
        str(args.preview_lines),
        "--max-targets",
        str(args.max_targets),
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


def build_subplans(
    *,
    targets: list[dict[str, Any]],
    max_subplans: int,
    subplan_size: int,
    execution_feedback: dict[str, Any],
) -> list[dict[str, Any]]:
    if not targets:
        return []

    ordered = sorted(
        list(targets),
        key=lambda item: (
            -_target_effective_rank(item, execution_feedback),
            -float(item.get("rank_score") or 0.0),
            -int(item.get("confidence") or 0),
        ),
    )
    consumed: set[str] = set()
    subplans: list[dict[str, Any]] = []

    for primary in ordered:
        primary_path = str(primary.get("path") or "")
        if not primary_path or primary_path in consumed:
            continue

        cluster = [primary]
        consumed.add(primary_path)
        for candidate in ordered:
            path = str(candidate.get("path") or "")
            if not path or path in consumed:
                continue
            if len(cluster) >= subplan_size:
                break
            same_family = _family_key(path) == _family_key(primary_path)
            linked = _link_score(candidate, primary_path) >= 1.5
            if same_family or linked:
                cluster.append(candidate)
                consumed.add(path)

        avg_confidence = round(
            sum(int(item.get("confidence") or 0) for item in cluster) / max(1, len(cluster)),
            2,
        )
        avg_rank_score = round(
            sum(float(item.get("rank_score") or 0.0) for item in cluster) / max(1, len(cluster)),
            4,
        )
        conflict_score, conflict_signals = _subplan_conflict_meta(cluster)
        link_strength = round(
            sum(_link_score(item, primary_path) for item in cluster if str(item.get("path") or "") != primary_path)
            / max(1, len(cluster) - 1),
            3,
        ) if len(cluster) > 1 else 0.0
        family_feedback = []
        cluster_families = sorted({str(item.get("family") or _family_key(str(item.get("path") or ""))) for item in cluster})
        for family in cluster_families:
            entry = ((execution_feedback.get("families") or {}).get(family) or {})
            if int(entry.get("samples", 0)) > 0:
                family_feedback.append({"family": family, **entry, "feedback_signal": _feedback_signal(entry)})
        pair_feedback: list[dict[str, Any]] = []
        pair_lookup = execution_feedback.get("family_pairs") or {}
        if len(cluster_families) >= 2:
            for a, b in itertools.combinations(cluster_families, 2):
                pair_key = _family_pair_key(a, b)
                pair_entry = pair_lookup.get(pair_key) or {}
                if int(pair_entry.get("samples", 0)) <= 0:
                    continue
                pair_feedback.append(
                    {
                        "pair": pair_key,
                        **pair_entry,
                        "feedback_signal": _pair_feedback_signal(pair_entry),
                    }
                )
        family_feedback_signal = round(
            sum(float(f.get("feedback_signal") or 0.0) for f in family_feedback) / max(1, len(family_feedback)),
            3,
        ) if family_feedback else 0.0
        pair_feedback_signal = round(
            sum(float(f.get("feedback_signal") or 0.0) for f in pair_feedback) / max(1, len(pair_feedback)),
            3,
        ) if pair_feedback else 0.0
        feedback_risk_penalty = round(
            sum(
                (
                    float(f.get("failure_rate") or 0.0)
                    + float(f.get("defer_rate") or 0.0)
                    + float(f.get("drop_rate") or 0.0)
                    + float(f.get("escalation_rate") or 0.0)
                )
                * 0.9
                for f in family_feedback
            ) / max(1, len(family_feedback)),
            3,
        ) if family_feedback else 0.0
        pair_risk_penalty = round(
            sum(
                (
                    float(p.get("failure_rate") or 0.0)
                    + float(p.get("defer_rate") or 0.0)
                    + float(p.get("drop_rate") or 0.0)
                    + float(p.get("escalation_rate") or 0.0)
                )
                * 1.1
                for p in pair_feedback
            ) / max(1, len(pair_feedback)),
            3,
        ) if pair_feedback else 0.0
        adjusted_conflict = round(conflict_score + feedback_risk_penalty + pair_risk_penalty, 3)
        yield_score = round(
            (avg_confidence * 0.85)
            + (avg_rank_score * 0.25)
            + (link_strength * 0.8)
            + family_feedback_signal
            + pair_feedback_signal
            - adjusted_conflict,
            3,
        )
        subplan_id = f"subplan-{len(subplans) + 1}"
        subplans.append(
            {
                "subplan_id": subplan_id,
                "primary": primary_path,
                "targets": [str(item.get("path")) for item in cluster],
                "target_meta": [
                    {
                        "path": str(item.get("path")),
                        "confidence": int(item.get("confidence") or 0),
                        "rank_score": float(item.get("rank_score") or 0.0),
                        "risk_bucket": _risk_bucket(int(item.get("confidence") or 0)),
                        "family": _family_key(str(item.get("path") or "")),
                    }
                    for item in cluster
                ],
                "confidence": avg_confidence,
                "rank_score": avg_rank_score,
                "size": len(cluster),
                "strategy": "linked_family_cluster",
                "risk_score": adjusted_conflict,
                "yield_score": yield_score,
                "conflict_signals": conflict_signals,
                "link_strength": link_strength,
                "execution_feedback": {
                    "family_feedback": family_feedback[:4],
                    "pair_feedback": pair_feedback[:4],
                    "family_feedback_signal": family_feedback_signal,
                    "pair_feedback_signal": pair_feedback_signal,
                    "feedback_risk_penalty": feedback_risk_penalty,
                    "pair_risk_penalty": pair_risk_penalty,
                },
            }
        )
        if len(subplans) >= max_subplans:
            break

    return sorted(
        subplans,
        key=lambda sp: (
            -float(sp.get("yield_score") or 0.0),
            float(sp.get("risk_score") or 0.0),
            -float(sp.get("confidence") or 0.0),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-6 planning helper")
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("query", nargs="+", help="Natural language probe for Stage-7")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--window", type=int, default=25)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--max-targets", type=int, default=9)
    parser.add_argument("--max-subplans", type=int, default=3)
    parser.add_argument("--subplan-size", type=int, default=3)
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument("--history-window", type=int, default=15)
    parser.add_argument("--feedback-window-days", type=int, default=30)
    parser.add_argument("--feedback-sample-limit", type=int, default=80)
    parser.add_argument("--notes", help="Optional notes/context for the plan")
    parser.add_argument(
        "--preferred-prefix",
        action="append",
        default=[],
        help="Preferred path prefix (repeatable) used for lane-aware ranking",
    )
    args = parser.parse_args()

    rag4_plan = run_rag4(args)
    targets = list(rag4_plan.get("targets", []))
    preferred_prefixes = [p for p in args.preferred_prefix if p]
    if preferred_prefixes:
        lane_aligned = [
            t for t in targets if any(str(t.get("path") or "").startswith(prefix) for prefix in preferred_prefixes)
        ]
        # Stage-7 should consume lane-clean candidates whenever available.
        if lane_aligned:
            targets = lane_aligned
    execution_feedback = load_execution_feedback(
        window_days=max(1, args.feedback_window_days),
        sample_limit=max(1, args.feedback_sample_limit),
    )
    subplans = build_subplans(
        targets=targets,
        max_subplans=max(1, args.max_subplans),
        subplan_size=max(1, args.subplan_size),
        execution_feedback=execution_feedback,
    )

    plan = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "plan_id": args.plan_id,
        "stage": "stage7",
        "query": " ".join(args.query),
        "subplans": subplans,
        "notes": args.notes,
        "provenance": {
            "query_tokens": args.query,
            "max_targets": args.max_targets,
            "max_subplans": args.max_subplans,
            "subplan_size": args.subplan_size,
            "preferred_prefixes": preferred_prefixes,
            "ranking_version": "rag10-v1-execution-cohort-cluster",
            "upstream_rag4_plan_id": rag4_plan.get("plan_id"),
            "upstream_ranking_version": (rag4_plan.get("provenance") or {}).get("ranking_version"),
            "retrieved_targets": len(targets),
            "emitted_subplans": len(subplans),
            "feedback_window_days": max(1, args.feedback_window_days),
            "feedback_sample_limit": max(1, args.feedback_sample_limit),
            "feedback_processed_plan_files": int(execution_feedback.get("processed_plan_files") or 0),
            "feedback_family_count": len((execution_feedback.get("families") or {})),
            "feedback_family_pair_count": len((execution_feedback.get("family_pairs") or {})),
        },
        "raw_payload": rag4_plan,
    }

    append_log(plan)
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
