#!/usr/bin/env python3
"""Operational learning loop from real Codex51 benchmark/campaign artifacts.

learning-v10 objective:
- convert real run artifacts into immediate local-first replay actions,
- produce training priorities tied to first-attempt quality deficits,
- keep model-vs-wrapper attribution explicit for next execution batches.
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
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    raw = ts[:-1] + "+00:00" if ts.endswith("Z") else ts
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _load_campaign_runs(path: Path, *, window_days: int) -> list[CampaignRun]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(1, window_days))
    runs: list[CampaignRun] = []
    for row in _read_jsonl(path):
        ts = _parse_ts(str(row.get("timestamp_utc") or ""))
        if ts is None or ts < cutoff:
            continue
        runs.append(
            CampaignRun(
                plan_id=str(row.get("plan_id") or ""),
                task_id=str(row.get("task_id") or ""),
                task_class=str(row.get("task_class") or "unknown"),
                timestamp_utc=str(row.get("timestamp_utc") or ""),
                success=bool(row.get("success")),
                rescue_count=int(row.get("rescue_count") or 0),
                escalation_count=int(row.get("escalation_count") or 0),
                guard_count=int(row.get("guard_count") or 0),
                first_attempt_quality_rate=float(row.get("first_attempt_quality_rate") or 0.0),
                attribution_primary=str(row.get("attribution_primary") or "mixed_gain"),
                command=str(row.get("command") or ""),
            )
        )
    runs.sort(key=lambda x: x.timestamp_utc, reverse=True)
    return runs


def _load_curation_counts(curation_dir: Path) -> dict[str, int]:
    files = {
        "training_examples": curation_dir / "training_examples.jsonl",
        "template_candidates": curation_dir / "template_candidates.jsonl",
        "guard_candidates": curation_dir / "guard_candidates.jsonl",
        "benchmark_wins": curation_dir / "benchmark_wins.jsonl",
        "failures_for_training": curation_dir / "failures_for_training.jsonl",
    }
    return {key: len(_read_jsonl(path)) for key, path in files.items()}


def _class_metrics_from_benchmark(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    rows = benchmark.get("class_metrics") or []
    return [row for row in rows if isinstance(row, dict)]


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
    counter = Counter(run.attribution_primary for run in runs)
    return dict(counter)


def _replay_queue(
    *,
    benchmark: dict[str, Any],
    class_metrics: list[dict[str, Any]],
    runs: list[CampaignRun],
    max_items: int,
) -> list[dict[str, Any]]:
    recurring = benchmark.get("metrics", {}).get("recurrence_signatures") or []
    recurrence_signatures = [str(item.get("signature") or "") for item in recurring if isinstance(item, dict)]
    weak_classes = {
        str(row.get("class_id") or "")
        for row in class_metrics
        if float(row.get("success_rate") or 0.0) < 0.7
        or float(row.get("first_attempt_quality_rate") or 0.0) < 0.5
        or float(row.get("escalation_rate") or 0.0) > 0.35
    }
    queued: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run in runs:
        if not run.task_id or run.task_id in seen:
            continue
        if run.task_class not in weak_classes and run.success:
            continue
        reason_parts = []
        if not run.success:
            reason_parts.append("recent_failure")
        if run.first_attempt_quality_rate < 0.5:
            reason_parts.append("low_first_attempt_quality")
        if run.escalation_count > 0:
            reason_parts.append("escalation_present")
        if recurrence_signatures:
            reason_parts.append("recurrence_present")
        queue_item = {
            "task_id": run.task_id,
            "task_class": run.task_class,
            "reason": ",".join(reason_parts) or "weak_class_performance",
            "replay_command": (
                f"python3 bin/local_replacement_campaign.py --config config/local_first_campaign.json "
                f"run --task-id {run.task_id} --profile normal --no-dry-run "
                f"--extra-arg=--preferred-prefix --extra-arg=bin/ "
                f"--extra-arg=--preferred-prefix --extra-arg=shell/ "
                f"--extra-arg=--worker-budget-grouped --extra-arg=40 "
                f"--extra-arg=--worker-budget-single --extra-arg=80"
            ),
            "source_plan_id": run.plan_id,
        }
        queued.append(queue_item)
        seen.add(run.task_id)
        if len(queued) >= max_items:
            break
    return queued


def _training_priority_queue(
    *,
    curation_dir: Path,
    class_metrics: list[dict[str, Any]],
    max_items: int,
) -> list[dict[str, Any]]:
    failures = _read_jsonl(curation_dir / "failures_for_training.jsonl")
    by_class_failures: dict[str, int] = defaultdict(int)
    for row in failures:
        cls = str(row.get("task_class") or "unknown")
        by_class_failures[cls] += 1

    quality_by_class = {
        str(row.get("class_id") or ""): float(row.get("first_attempt_quality_rate") or 0.0)
        for row in class_metrics
    }
    sorted_classes = sorted(
        by_class_failures.keys(),
        key=lambda cls: (-by_class_failures[cls], quality_by_class.get(cls, 1.0)),
    )
    queue: list[dict[str, Any]] = []
    for cls in sorted_classes[:max_items]:
        queue.append(
            {
                "task_class": cls,
                "failure_examples": by_class_failures[cls],
                "first_attempt_quality_rate": quality_by_class.get(cls, 0.0),
                "action": "curate_negative_and_positive_pair_set",
                "output_artifact": f"artifacts/codex51/learning/curriculum_{cls}.jsonl",
            }
        )
    return queue


def _next_build_step(
    *,
    benchmark_metrics: dict[str, Any],
    local_share: float,
    replay_queue: list[dict[str, Any]],
) -> str:
    recurrence_rate = float(benchmark_metrics.get("recurrence_rate") or 0.0)
    first_attempt = float(benchmark_metrics.get("first_attempt_quality_rate") or 0.0)
    if recurrence_rate > 0.35 and replay_queue:
        top = replay_queue[0]
        return (
            "Run blocker-first replay on highest-failure class task "
            f"({top['task_id']} / {top['task_class']}) and fix first boundary before any new ladder move."
        )
    if first_attempt < 0.5:
        return "Execute first_attempt_only slice on weakest class and convert top failure signature into guard+template pair."
    if local_share < 0.8:
        return "Increase local-first share by moving one additional bounded complex class to default local routing."
    return "Advance manager10-v1 hierarchical policy memory using the replay queue outcomes as strategy priors."


def build_learning_report(
    *,
    benchmark: dict[str, Any],
    runs: list[CampaignRun],
    curation_dir: Path,
    manifest: dict[str, Any],
    max_replay: int,
    max_training: int,
) -> dict[str, Any]:
    metrics = benchmark.get("metrics") if isinstance(benchmark.get("metrics"), dict) else {}
    class_metrics = _class_metrics_from_benchmark(benchmark)
    local_share = _local_first_share(runs)
    replay_queue = _replay_queue(
        benchmark=benchmark,
        class_metrics=class_metrics,
        runs=runs,
        max_items=max_replay,
    )
    training_queue = _training_priority_queue(
        curation_dir=curation_dir,
        class_metrics=class_metrics,
        max_items=max_training,
    )
    learning_version = _learning_status_from_manifest(manifest)
    curation_counts = _load_curation_counts(curation_dir)
    report = {
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "learning_subsystem": learning_version,
        "benchmark_metrics": {
            "success_rate": float(metrics.get("success_rate") or 0.0),
            "rescue_rate": float(metrics.get("rescue_rate") or 0.0),
            "escalation_rate": float(metrics.get("escalation_rate") or 0.0),
            "recurrence_rate": float(metrics.get("recurrence_rate") or 0.0),
            "first_attempt_quality_rate": float(metrics.get("first_attempt_quality_rate") or 0.0),
        },
        "local_first_share_window": local_share,
        "campaign_window_runs": len(runs),
        "attribution_mix": _attribution_mix(runs),
        "curation_counts": curation_counts,
        "replay_queue": replay_queue,
        "training_priority_queue": training_queue,
        "next_high_leverage_step": _next_build_step(
            benchmark_metrics=metrics,
            local_share=local_share,
            replay_queue=replay_queue,
        ),
    }
    return report


def _report_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Codex51 Learning Loop")
    lines.append("")
    lines.append(f"- generated_at_utc: {report['generated_at_utc']}")
    lines.append(f"- learning_version: {report['learning_subsystem'].get('current_version', 'untracked')}")
    lines.append(f"- status: {report['learning_subsystem'].get('status', 'held')}")
    lines.append(f"- campaign_window_runs: {report['campaign_window_runs']}")
    lines.append(f"- local_first_share_window: {report['local_first_share_window']}")
    lines.append("")
    lines.append("## Benchmark Snapshot")
    for key, value in report["benchmark_metrics"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Attribution Mix")
    attribution = report.get("attribution_mix") or {}
    if not attribution:
        lines.append("- none")
    else:
        for key, value in sorted(attribution.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Replay Queue")
    replay = report.get("replay_queue") or []
    if not replay:
        lines.append("- none")
    else:
        for row in replay:
            lines.append(f"- {row['task_id']} ({row['task_class']}): {row['reason']}")
            lines.append(f"  command: {row['replay_command']}")
    lines.append("")
    lines.append("## Training Priority Queue")
    training = report.get("training_priority_queue") or []
    if not training:
        lines.append("- none")
    else:
        for row in training:
            lines.append(
                f"- {row['task_class']}: failures={row['failure_examples']} "
                f"first_attempt_quality_rate={row['first_attempt_quality_rate']}"
            )
    lines.append("")
    lines.append("## Next Step")
    lines.append(f"- {report['next_high_leverage_step']}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run learning-v10 loop from Codex51 artifacts.")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--campaign-runs", default=str(DEFAULT_CAMPAIGN_RUNS))
    parser.add_argument("--curation-dir", default=str(DEFAULT_CURATION))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--max-replay", type=int, default=3)
    parser.add_argument("--max-training", type=int, default=3)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_path = Path(args.benchmark).resolve()
    if not benchmark_path.exists():
        print(f"missing benchmark: {benchmark_path}")
        return 2
    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"missing manifest: {manifest_path}")
        return 2
    curation_dir = Path(args.curation_dir).resolve()
    if not curation_dir.exists():
        print(f"missing curation dir: {curation_dir}")
        return 2

    benchmark = _read_json(benchmark_path)
    manifest = _read_json(manifest_path)
    runs = _load_campaign_runs(Path(args.campaign_runs).resolve(), window_days=max(1, args.window_days))
    report = build_learning_report(
        benchmark=benchmark,
        runs=runs,
        curation_dir=curation_dir,
        manifest=manifest,
        max_replay=max(1, args.max_replay),
        max_training=max(1, args.max_training),
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
