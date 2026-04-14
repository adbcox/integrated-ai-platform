#!/usr/bin/env python3
"""Export benchmark/campaign artifacts into training/template/guard curation sets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = REPO_ROOT / "artifacts" / "codex51" / "benchmark" / "latest.json"
DEFAULT_CAMPAIGN_RUNS = REPO_ROOT / "artifacts" / "codex51" / "campaign" / "runs.jsonl"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "codex51" / "curation"
DEFAULT_PLAN_DIR = REPO_ROOT / "artifacts" / "manager6" / "plans"


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


def _plan_payload(plan_id: str, plan_dir: Path) -> dict[str, Any]:
    plan_path = plan_dir / f"{plan_id}.json"
    if not plan_path.exists():
        return {}
    data = _read_json(plan_path)
    history = data.get("history") or []
    for row in reversed(history):
        if str(row.get("event_type") or "") == "attempt_finished":
            return row.get("plan_payload") or data.get("plan_payload") or {}
    return data.get("plan_payload") or {}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=True) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def build_exports(
    *,
    benchmark: dict[str, Any],
    campaign_runs: list[dict[str, Any]],
    plan_dir: Path,
) -> dict[str, Any]:
    recurrence = {
        item.get("signature"): int(item.get("count", 0))
        for item in (benchmark.get("metrics", {}).get("recurrence_signatures") or [])
        if item.get("signature")
    }
    benchmark_items = {
        item.get("plan_id"): item
        for item in (benchmark.get("task_set", {}).get("items") or [])
        if item.get("plan_id")
    }

    training_examples: list[dict[str, Any]] = []
    template_candidates: list[dict[str, Any]] = []
    guard_candidates: list[dict[str, Any]] = []
    benchmark_wins: list[dict[str, Any]] = []
    failures_for_training: list[dict[str, Any]] = []

    for run in campaign_runs:
        plan_id = str(run.get("plan_id") or "")
        if not plan_id:
            continue
        payload = _plan_payload(plan_id, plan_dir)
        query = str(payload.get("query") or "")
        reconciliation = payload.get("stage_reconciliation") if isinstance(payload.get("stage_reconciliation"), dict) else {}
        recoveries = [x for x in (payload.get("recoveries") or []) if isinstance(x, dict)]
        statuses = [x for x in (run.get("plan_result", {}).get("status_count"),)]

        base_row = {
            "schema_version": "1",
            "plan_id": plan_id,
            "timestamp_utc": str(run.get("timestamp_utc") or ""),
            "task_id": str(run.get("task_id") or ""),
            "task_class": str(run.get("task_class") or ""),
            "query": query,
            "attribution_profile": str(run.get("attribution_profile") or "normal"),
            "attribution_primary": str(run.get("attribution_primary") or "mixed_gain"),
            "ranking_version": str(run.get("ranking_version") or ""),
            "first_attempt_quality_rate": float(run.get("first_attempt_quality_rate") or 0.0),
            "rescue_count": int(run.get("rescue_count") or 0),
            "escalation_count": int(run.get("escalation_count") or 0),
            "guard_count": int(run.get("guard_count") or 0),
            "success": bool(run.get("success")),
            "stage_reconciliation": reconciliation,
            "recoveries": recoveries,
            "benchmark_member": bool(plan_id in benchmark_items),
        }

        if base_row["success"] and base_row["first_attempt_quality_rate"] >= 1.0 and base_row["rescue_count"] == 0:
            template = {
                **base_row,
                "curation_destination": "template_candidate",
                "template_reason": "high first-attempt quality without rescue",
            }
            template_candidates.append(template)
            benchmark_wins.append(
                {
                    **base_row,
                    "curation_destination": "benchmark_win",
                    "win_reason": "success with model-forward execution profile",
                }
            )
            training_examples.append(
                {
                    **base_row,
                    "curation_destination": "training_positive",
                    "training_reason": "successful bounded complex local execution",
                }
            )
        elif base_row["success"]:
            training_examples.append(
                {
                    **base_row,
                    "curation_destination": "training_positive_assisted",
                    "training_reason": "success with rescue/escalation signals",
                }
            )
        else:
            failure_signature = ""
            if base_row["benchmark_member"]:
                failure_signature = next(
                    (
                        sig
                        for sig in recurrence.keys()
                        if sig and sig in str(run.get("plan_result", {}))
                    ),
                    "",
                )
            failure_row = {
                **base_row,
                "curation_destination": "training_negative",
                "training_reason": "local run failure",
                "recurrence_signature": failure_signature,
                "recurrence_count": int(recurrence.get(failure_signature, 0)) if failure_signature else 0,
            }
            failures_for_training.append(failure_row)

        if base_row["guard_count"] > 0:
            guard_candidates.append(
                {
                    **base_row,
                    "curation_destination": "guard_rule_candidate",
                    "guard_reason": "guard/defer/preflight signal observed",
                }
            )

    return {
        "training_examples": training_examples,
        "template_candidates": template_candidates,
        "guard_candidates": guard_candidates,
        "benchmark_wins": benchmark_wins,
        "failures_for_training": failures_for_training,
    }


def build_summary(exports: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    primary_counter = Counter()
    for key in ("training_examples", "template_candidates", "guard_candidates", "benchmark_wins", "failures_for_training"):
        for row in exports.get(key, []):
            primary_counter[str(row.get("attribution_primary") or "unknown")] += 1
    return {
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": {k: len(v) for k, v in exports.items()},
        "attribution_primary_counts": dict(primary_counter),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Codex51 benchmark/campaign curation artifacts.")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--campaign-runs", default=str(DEFAULT_CAMPAIGN_RUNS))
    parser.add_argument("--plan-dir", default=str(DEFAULT_PLAN_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--json-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_path = Path(args.benchmark).resolve()
    if not benchmark_path.exists():
        print(f"benchmark file missing: {benchmark_path}")
        return 2
    benchmark = _read_json(benchmark_path)
    campaign_runs = _read_jsonl(Path(args.campaign_runs).resolve())
    exports = build_exports(
        benchmark=benchmark,
        campaign_runs=campaign_runs,
        plan_dir=Path(args.plan_dir).resolve(),
    )
    summary = build_summary(exports)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out_dir / "training_examples.jsonl", exports["training_examples"])
    _write_jsonl(out_dir / "template_candidates.jsonl", exports["template_candidates"])
    _write_jsonl(out_dir / "guard_candidates.jsonl", exports["guard_candidates"])
    _write_jsonl(out_dir / "benchmark_wins.jsonl", exports["benchmark_wins"])
    _write_jsonl(out_dir / "failures_for_training.jsonl", exports["failures_for_training"])
    (out_dir / "latest.json").write_text(
        json.dumps({"summary": summary, "outputs": {k: f"{k}.jsonl" for k in exports}}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.json_only:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("# Codex51 Curation Export")
        print(f"- generated_at_utc: {summary['generated_at_utc']}")
        for key, value in summary["counts"].items():
            print(f"- {key}: {value}")
        for key, value in summary["attribution_primary_counts"].items():
            print(f"- attribution_primary::{key}: {value}")
        print(f"- out_dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
