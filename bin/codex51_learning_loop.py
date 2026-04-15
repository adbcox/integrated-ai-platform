#!/usr/bin/env python3
"""Operational learning loop from real Codex51 artifacts.

learning-v11 objective:
- rank weak classes deterministically from real benchmark/campaign evidence,
- split action candidates (guard/manager/retrieval/training/template),
- emit prioritized replay + improvement targets with model-vs-wrapper attribution.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = REPO_ROOT / "artifacts" / "codex51" / "benchmark" / "latest.json"
DEFAULT_CAMPAIGN_RUNS = REPO_ROOT / "artifacts" / "codex51" / "campaign" / "runs.jsonl"
DEFAULT_CURATION = REPO_ROOT / "artifacts" / "codex51" / "curation"
DEFAULT_MANIFEST = REPO_ROOT / "config" / "promotion_manifest.json"
DEFAULT_ATTRIBUTION = REPO_ROOT / "artifacts" / "codex51" / "attribution" / "latest.json"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "codex51" / "learning"


@dataclass(frozen=True)
class CampaignRun:
    plan_id: str
    task_id: str
    task_class: str
    timestamp_utc: str
    success: bool
    rescue_count: int
    escalation_count: int
    guard_count: int
    first_attempt_quality_rate: float
    attribution_primary: str
    attribution_bucket: str
    ranking_version: str
    families: tuple[str, ...]
    command: str


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
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


def _load_campaign_runs(path: Path, *, window_days: int) -> list[CampaignRun]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(1, window_days))
    runs: list[CampaignRun] = []
    for row in _read_jsonl(path):
        ts = _parse_ts(str(row.get("timestamp_utc") or ""))
        if ts is None or ts < cutoff:
            continue
        families = tuple(str(item).strip() for item in (row.get("families") or []) if str(item).strip())
        runs.append(
            CampaignRun(
                plan_id=str(row.get("plan_id") or ""),
                task_id=str(row.get("task_id") or ""),
                task_class=str(row.get("task_class") or "unknown"),
                timestamp_utc=str(row.get("timestamp_utc") or ""),
                success=bool(row.get("success")),
                rescue_count=_safe_int(row.get("rescue_count")),
                escalation_count=_safe_int(row.get("escalation_count")),
                guard_count=_safe_int(row.get("guard_count")),
                first_attempt_quality_rate=_safe_float(row.get("first_attempt_quality_rate")),
                attribution_primary=str(row.get("attribution_primary") or "mixed_gain"),
                attribution_bucket=str(row.get("attribution_bucket") or "mixed_or_shared"),
                ranking_version=str(row.get("ranking_version") or ""),
                families=families,
                command=str(row.get("command") or ""),
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


def _class_metrics_from_benchmark(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    rows = benchmark.get("class_metrics")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


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


def _weak_class_summary(benchmark_classes: list[dict[str, Any]], runs: list[CampaignRun]) -> list[dict[str, Any]]:
    run_by_class: dict[str, list[CampaignRun]] = defaultdict(list)
    for run in runs:
        run_by_class[run.task_class].append(run)

    summary: list[dict[str, Any]] = []
    for row in benchmark_classes:
        class_id = str(row.get("class_id") or "unknown")
        class_runs = run_by_class.get(class_id, [])
        task_count = max(1, _safe_int(row.get("task_count"), 1))
        success_rate = _safe_float(row.get("success_rate"))
        rescue_rate = _safe_float(row.get("rescue_rate"))
        escalation_rate = _safe_float(row.get("escalation_rate"))
        recurrence_rate = _safe_float(row.get("recurrence_rate"))
        first_attempt_quality_rate = _safe_float(row.get("first_attempt_quality_rate"))
        model_pressure = max(0.0, 1.0 - first_attempt_quality_rate)
        wrapper_pressure = min(1.0, rescue_rate + escalation_rate + recurrence_rate)
        if class_runs:
            class_run_model_pressure = sum(1.0 - r.first_attempt_quality_rate for r in class_runs) / len(class_runs)
            class_run_wrapper_pressure = sum(
                (1 if (r.rescue_count > 0 or r.escalation_count > 0 or r.guard_count > 0) else 0) for r in class_runs
            ) / len(class_runs)
            model_pressure = round((model_pressure + class_run_model_pressure) / 2.0, 3)
            wrapper_pressure = round((wrapper_pressure + class_run_wrapper_pressure) / 2.0, 3)
        else:
            model_pressure = round(model_pressure, 3)
            wrapper_pressure = round(wrapper_pressure, 3)

        weakness_score = round(
            (1.0 - success_rate) * 4.0
            + recurrence_rate * 3.0
            + escalation_rate * 2.0
            + rescue_rate * 2.0
            + max(0.0, 0.7 - first_attempt_quality_rate) * 2.5
            + model_pressure,
            3,
        )
        if model_pressure > wrapper_pressure + 0.1:
            dominant_weakness = "model"
        elif wrapper_pressure > model_pressure + 0.1:
            dominant_weakness = "wrapper"
        else:
            dominant_weakness = "mixed"

        summary.append(
            {
                "class_id": class_id,
                "class_label": str(row.get("class_label") or class_id),
                "task_count": task_count,
                "success_rate": round(success_rate, 3),
                "rescue_rate": round(rescue_rate, 3),
                "escalation_rate": round(escalation_rate, 3),
                "recurrence_rate": round(recurrence_rate, 3),
                "first_attempt_quality_rate": round(first_attempt_quality_rate, 3),
                "weakness_score": weakness_score,
                "model_pressure": model_pressure,
                "wrapper_pressure": wrapper_pressure,
                "dominant_weakness": dominant_weakness,
            }
        )
    summary.sort(key=lambda item: item["weakness_score"], reverse=True)
    return summary


def _weak_first_attempt_paths(runs: list[CampaignRun], *, max_items: int) -> list[dict[str, Any]]:
    ordered = sorted(
        runs,
        key=lambda run: (
            run.first_attempt_quality_rate,
            -(run.rescue_count + run.escalation_count + run.guard_count),
            run.timestamp_utc,
        ),
    )
    out: list[dict[str, Any]] = []
    for run in ordered[: max(1, max_items)]:
        out.append(
            {
                "plan_id": run.plan_id,
                "task_id": run.task_id,
                "task_class": run.task_class,
                "timestamp_utc": run.timestamp_utc,
                "first_attempt_quality_rate": round(run.first_attempt_quality_rate, 3),
                "rescue_count": run.rescue_count,
                "escalation_count": run.escalation_count,
                "guard_count": run.guard_count,
                "attribution_primary": run.attribution_primary,
                "attribution_bucket": run.attribution_bucket,
            }
        )
    return out


def _replay_queue(
    *,
    weak_classes: list[dict[str, Any]],
    runs: list[CampaignRun],
    max_items: int,
) -> list[dict[str, Any]]:
    weak_class_ids = {row["class_id"] for row in weak_classes[: max(1, min(len(weak_classes), 5))]}
    candidates: list[CampaignRun] = []
    for run in runs:
        if run.task_class not in weak_class_ids:
            continue
        if run.first_attempt_quality_rate >= 0.8 and run.success:
            continue
        candidates.append(run)
    candidates.sort(
        key=lambda run: (
            run.first_attempt_quality_rate,
            -(run.rescue_count + run.escalation_count + run.guard_count),
            run.timestamp_utc,
        )
    )

    queued: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run in candidates:
        if not run.task_id or run.task_id in seen:
            continue
        reason: list[str] = []
        if not run.success:
            reason.append("recent_failure")
        if run.first_attempt_quality_rate < 0.5:
            reason.append("low_first_attempt_quality")
        if run.rescue_count > 0:
            reason.append("rescue_dependency")
        if run.escalation_count > 0:
            reason.append("escalation_present")
        if run.guard_count > 0:
            reason.append("guard_dependency")
        queued.append(
            {
                "task_id": run.task_id,
                "task_class": run.task_class,
                "source_plan_id": run.plan_id,
                "reason": ",".join(reason) if reason else "weak_class_priority",
                "replay_command": (
                    "python3 bin/local_replacement_campaign.py --config config/local_first_campaign.json "
                    f"run --task-id {run.task_id} --profile normal --no-dry-run "
                    "--extra-arg=--preferred-prefix --extra-arg=bin/ "
                    "--extra-arg=--preferred-prefix --extra-arg=shell/ "
                    "--extra-arg=--worker-budget-grouped --extra-arg=40 "
                    "--extra-arg=--worker-budget-single --extra-arg=80"
                ),
            }
        )
        seen.add(run.task_id)
        if len(queued) >= max_items:
            break
    return queued


def _candidate_splits(
    *,
    curation_rows: dict[str, list[dict[str, Any]]],
    weak_classes: list[dict[str, Any]],
    max_items: int,
) -> dict[str, list[dict[str, Any]]]:
    weak_class_ids = {row["class_id"] for row in weak_classes[: max(1, min(len(weak_classes), 6))]}
    failures = curation_rows.get("failures_for_training", [])
    training_examples = curation_rows.get("training_examples", [])
    guard_rows = curation_rows.get("guard_candidates", [])
    benchmark_wins = curation_rows.get("benchmark_wins", [])
    existing_templates = curation_rows.get("template_candidates", [])

    def _compact(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan_id": str(row.get("plan_id") or ""),
            "task_id": str(row.get("task_id") or ""),
            "task_class": str(row.get("task_class") or "unknown"),
            "first_attempt_quality_score": round(_safe_float(row.get("first_attempt_quality_score")), 3),
            "rescue_count": _safe_int(row.get("rescue_count")),
            "escalation_count": _safe_int(row.get("escalation_count")),
            "guard_count": _safe_int(row.get("guard_count")),
            "attribution_primary": str(row.get("attribution_primary") or "mixed_gain"),
            "reason": str(
                row.get("training_reason")
                or row.get("guard_reason")
                or row.get("recurrence_signature")
                or "artifact_signal"
            ),
        }

    guard_candidates: list[dict[str, Any]] = []
    seen_guard: set[str] = set()
    for row in guard_rows:
        cls = str(row.get("task_class") or "unknown")
        if cls not in weak_class_ids:
            continue
        key = str(row.get("plan_id") or "")
        if not key or key in seen_guard:
            continue
        guard_candidates.append(_compact(row))
        seen_guard.add(key)
        if len(guard_candidates) >= max_items:
            break

    manager_rule_candidates: list[dict[str, Any]] = []
    retrieval_rule_candidates: list[dict[str, Any]] = []
    training_candidates: list[dict[str, Any]] = []
    seen_mgr: set[str] = set()
    seen_rag: set[str] = set()
    seen_train: set[str] = set()

    ordered_failures = sorted(
        failures,
        key=lambda row: (
            _safe_float(row.get("first_attempt_quality_score"), 1.0),
            -(_safe_int(row.get("rescue_count")) + _safe_int(row.get("escalation_count"))),
        ),
    )
    for row in ordered_failures:
        cls = str(row.get("task_class") or "unknown")
        if cls not in weak_class_ids:
            continue
        plan_id = str(row.get("plan_id") or "")
        if not plan_id:
            continue

        reason = str(row.get("recurrence_signature") or row.get("training_reason") or "")
        compact = _compact(row)
        if (
            ("deferred_worker_budget" in reason or _safe_int(row.get("rescue_count")) > 0 or _safe_int(row.get("escalation_count")) > 0)
            and plan_id not in seen_mgr
            and len(manager_rule_candidates) < max_items
        ):
            manager_rule_candidates.append(compact)
            seen_mgr.add(plan_id)

        if (
            (
                "retrieval" in cls
                or str(row.get("attribution_primary") or "") in {"retrieval_gain", "mixed_gain"}
                or "anchor" in str(row.get("query") or "").lower()
            )
            and plan_id not in seen_rag
            and len(retrieval_rule_candidates) < max_items
        ):
            retrieval_rule_candidates.append(compact)
            seen_rag.add(plan_id)

        if plan_id not in seen_train and len(training_candidates) < max_items:
            training_candidates.append(compact)
            seen_train.add(plan_id)

    template_candidates: list[dict[str, Any]] = []
    seen_tpl: set[str] = set()
    template_source = benchmark_wins + existing_templates + training_examples
    template_source_sorted = sorted(
        template_source,
        key=lambda row: (
            -_safe_float(row.get("first_attempt_quality_score"), 0.0),
            _safe_int(row.get("rescue_count")) + _safe_int(row.get("escalation_count")) + _safe_int(row.get("guard_count")),
        ),
    )
    for row in template_source_sorted:
        cls = str(row.get("task_class") or "unknown")
        if cls not in weak_class_ids:
            continue
        plan_id = str(row.get("plan_id") or "")
        if not plan_id or plan_id in seen_tpl:
            continue
        quality = _safe_float(row.get("first_attempt_quality_score"), 0.0)
        if quality < 0.8:
            continue
        if _safe_int(row.get("rescue_count")) > 0 or _safe_int(row.get("escalation_count")) > 0 or _safe_int(row.get("guard_count")) > 0:
            continue
        template_candidates.append(_compact(row))
        seen_tpl.add(plan_id)
        if len(template_candidates) >= max_items:
            break

    return {
        "guard_rule_candidates": guard_candidates,
        "manager_rule_candidates": manager_rule_candidates,
        "retrieval_rule_candidates": retrieval_rule_candidates,
        "training_example_candidates": training_candidates,
        "template_promotion_candidates": template_candidates,
    }


def _model_vs_wrapper_summary(weak_classes: list[dict[str, Any]], attribution: dict[str, Any]) -> dict[str, Any]:
    model_dominant = [row["class_id"] for row in weak_classes if row.get("dominant_weakness") == "model"]
    wrapper_dominant = [row["class_id"] for row in weak_classes if row.get("dominant_weakness") == "wrapper"]
    mixed = [row["class_id"] for row in weak_classes if row.get("dominant_weakness") == "mixed"]

    campaign_agg = attribution.get("campaign_aggregate") if isinstance(attribution.get("campaign_aggregate"), dict) else {}
    bucket_counts = campaign_agg.get("attribution_bucket_counts") if isinstance(campaign_agg.get("attribution_bucket_counts"), dict) else {}
    local_with_assist = int(bucket_counts.get("local_with_manager_rescue", 0)) + int(bucket_counts.get("local_with_rag_assist", 0))
    codex_or_manual = int(bucket_counts.get("codex_or_manual_primary", 0))
    mixed_or_shared = int(bucket_counts.get("mixed_or_shared", 0))

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
            "mixed_or_shared": mixed_or_shared,
        },
    }


def _next_step_recommendations(
    *,
    weak_classes: list[dict[str, Any]],
    replay_queue: list[dict[str, Any]],
    candidate_splits: dict[str, list[dict[str, Any]]],
    model_wrapper: dict[str, Any],
) -> list[str]:
    recs: list[str] = []
    if weak_classes:
        top = weak_classes[0]
        recs.append(
            f"Replay weakest class first: {top['class_id']} (weakness_score={top['weakness_score']}, dominant={top['dominant_weakness']})."
        )
    if replay_queue:
        recs.append(
            f"Execute blocker-first replay task: {replay_queue[0]['task_id']} ({replay_queue[0]['reason']})."
        )
    if candidate_splits.get("guard_rule_candidates"):
        recs.append("Convert top guard candidate into a deterministic pre-dispatch guard rule before next campaign batch.")
    if candidate_splits.get("manager_rule_candidates"):
        recs.append("Apply manager strategy memory/routing adjustment for top manager-rule candidate to reduce repeat rescue/escalation.")
    if candidate_splits.get("retrieval_rule_candidates"):
        recs.append("Apply retrieval anchor/grouping refinement for top retrieval-rule candidate and rerun first_attempt_only path.")
    if model_wrapper.get("dominant_gap") == "model_weakness":
        recs.append("Prioritize training-example curation for model-dominant weak classes before broad wrapper changes.")
    elif model_wrapper.get("dominant_gap") == "wrapper_weakness":
        recs.append("Prioritize guard/manager/retrieval rule updates before adding new training batches.")
    if not recs:
        recs.append("No high-pressure weak class detected; run next harder first_attempt_only mixed-family slice.")
    return recs


def build_learning_report(
    *,
    benchmark: dict[str, Any],
    runs: list[CampaignRun],
    curation_rows: dict[str, list[dict[str, Any]]],
    manifest: dict[str, Any],
    attribution: dict[str, Any],
    max_replay: int,
    max_candidates: int,
) -> dict[str, Any]:
    metrics = benchmark.get("metrics") if isinstance(benchmark.get("metrics"), dict) else {}
    benchmark_classes = _class_metrics_from_benchmark(benchmark)
    weak_classes = _weak_class_summary(benchmark_classes, runs)
    weak_paths = _weak_first_attempt_paths(runs, max_items=max_candidates)
    replay_queue = _replay_queue(weak_classes=weak_classes, runs=runs, max_items=max_replay)
    candidate_splits = _candidate_splits(
        curation_rows=curation_rows,
        weak_classes=weak_classes,
        max_items=max_candidates,
    )
    model_wrapper = _model_vs_wrapper_summary(weak_classes, attribution)
    recommendations = _next_step_recommendations(
        weak_classes=weak_classes,
        replay_queue=replay_queue,
        candidate_splits=candidate_splits,
        model_wrapper=model_wrapper,
    )

    learning_version = _learning_status_from_manifest(manifest)
    curation_counts = {key: len(rows) for key, rows in curation_rows.items()}
    report = {
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
        "weak_class_summary": weak_classes,
        "weak_first_attempt_paths": weak_paths,
        "prioritized_replay_queue": replay_queue,
        "candidate_splits": candidate_splits,
        "model_vs_wrapper_summary": model_wrapper,
        "curation_counts": curation_counts,
        "next_recommended_targets": recommendations,
        "source_artifacts": {
            "benchmark": str(DEFAULT_BENCHMARK),
            "campaign_runs": str(DEFAULT_CAMPAIGN_RUNS),
            "curation_dir": str(DEFAULT_CURATION),
            "attribution": str(DEFAULT_ATTRIBUTION),
        },
    }
    return report


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
    lines.append("## Benchmark Snapshot")
    for key, value in (report.get("benchmark_metrics") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Weak Classes")
    weak = report.get("weak_class_summary") or []
    if not weak:
        lines.append("- none")
    else:
        for row in weak[:5]:
            lines.append(
                f"- {row['class_id']}: weakness_score={row['weakness_score']} "
                f"first_attempt_quality_rate={row['first_attempt_quality_rate']} "
                f"dominant={row['dominant_weakness']}"
            )
    lines.append("")
    lines.append("## Candidate Splits")
    splits = report.get("candidate_splits") or {}
    for key in [
        "guard_rule_candidates",
        "manager_rule_candidates",
        "retrieval_rule_candidates",
        "training_example_candidates",
        "template_promotion_candidates",
    ]:
        lines.append(f"- {key}: {len(splits.get(key) or [])}")
    lines.append("")
    lines.append("## Prioritized Replay Queue")
    queue = report.get("prioritized_replay_queue") or []
    if not queue:
        lines.append("- none")
    else:
        for row in queue:
            lines.append(f"- {row['task_id']} ({row['task_class']}): {row['reason']}")
    lines.append("")
    lines.append("## Model Vs Wrapper")
    mvsw = report.get("model_vs_wrapper_summary") or {}
    lines.append(f"- dominant_gap: {mvsw.get('dominant_gap', 'mixed')}")
    lines.append(f"- model_dominant_classes: {', '.join(mvsw.get('model_dominant_classes') or []) or 'none'}")
    lines.append(f"- wrapper_dominant_classes: {', '.join(mvsw.get('wrapper_dominant_classes') or []) or 'none'}")
    lines.append("")
    lines.append("## Next Recommended Targets")
    for item in report.get("next_recommended_targets") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run learning-v11 loop from Codex51 artifacts.")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--campaign-runs", default=str(DEFAULT_CAMPAIGN_RUNS))
    parser.add_argument("--curation-dir", default=str(DEFAULT_CURATION))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--attribution", default=str(DEFAULT_ATTRIBUTION))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--max-replay", type=int, default=5)
    parser.add_argument("--max-candidates", type=int, default=5)
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
    runs = _load_campaign_runs(campaign_runs_path, window_days=max(1, args.window_days))
    curation_rows = _load_curation_rows(curation_dir)

    report = build_learning_report(
        benchmark=benchmark,
        runs=runs,
        curation_rows=curation_rows,
        manifest=manifest,
        attribution=attribution,
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

    if args.json_only:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_report_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
