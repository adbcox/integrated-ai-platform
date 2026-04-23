#!/usr/bin/env python3
"""Summarize promotion readiness for the candidate lane."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, deque
from datetime import datetime, timedelta
from _datetime_compat import UTC
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
DEFAULT_MANAGER_TRACE = REPO_ROOT / "artifacts" / "manager4" / "traces.jsonl"
DEFAULT_STAGE5_TRACE = REPO_ROOT / "artifacts" / "stage5_manager" / "traces.jsonl"


def read_traces(path: Path) -> Iterable[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def is_candidate_batch(batch_file: str | None) -> bool:
    if not batch_file:
        return False
    return Path(batch_file).name.startswith("stage5_candidate_job")


def parse_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def summarize_candidate_activity(
    trace_path: Path,
    lane_name: str,
    window_days: int | None = None,
) -> dict:
    stats = Counter()
    recent = deque(maxlen=5)
    cutoff = None
    if window_days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
    for entry in read_traces(trace_path):
        if entry.get("lane") != lane_name:
            continue
        timestamp = parse_timestamp(entry.get("timestamp"))
        if cutoff and (timestamp is None or timestamp < cutoff):
            continue
        batch_file = entry.get("batch_file")
        real = is_candidate_batch(batch_file)
        retcode = entry.get("return_code")
        outcome = "successes" if retcode == 0 else "failures"
        if real:
            stats[f"real_{outcome}"] += 1
            recent.appendleft(
                {
                    "timestamp": entry.get("timestamp"),
                    "target": entry.get("target"),
                    "stage": entry.get("stage"),
                    "return_code": retcode,
                    "batch_file": batch_file,
                }
            )
        else:
            stats[f"guard_{outcome}"] += 1
    stats["total_successes"] = stats["real_successes"] + stats["guard_successes"]
    stats["total_failures"] = stats["real_failures"] + stats["guard_failures"]
    return {"stats": stats, "recent": list(recent)}


def summarize_stage5_commits(trace_path: Path) -> list[dict]:
    recent_commits = deque(maxlen=3)
    for entry in read_traces(trace_path):
        recent_commits.appendleft(
            {
                "timestamp": entry.get("timestamp"),
                "job_id": entry.get("job_id"),
                "targets": entry.get("targets"),
                "operations": entry.get("operations"),
                "total_added": entry.get("total_added"),
                "total_deleted": entry.get("total_deleted"),
            }
        )
    return list(recent_commits)


def verdict(stats: Counter, criteria: dict) -> tuple[str, list[str]]:
    required_successes = int(criteria.get("candidate_success_threshold", 0))
    failure_budget = int(criteria.get("candidate_failure_budget", 0))
    reasons: list[str] = []
    if stats["real_successes"] < required_successes:
        reasons.append(
            f"Needs {required_successes - stats['real_successes']} more successful candidate jobs."
        )
    if stats["real_failures"] > failure_budget:
        reasons.append(f"Exceeded failure budget by {stats['real_failures'] - failure_budget}.")
    if not reasons:
        return "promotable", []
    return "needs-more-data", reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate promotion readiness for the candidate lane.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--manager-trace", default=str(DEFAULT_MANAGER_TRACE))
    parser.add_argument("--stage5-trace", default=str(DEFAULT_STAGE5_TRACE))
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manager_trace = Path(args.manager_trace).resolve()
    stage5_trace = Path(args.stage5_trace).resolve()

    manifest = load_manifest(manifest_path)
    manifest_data = manifest.data
    candidate_lane = resolve_versions_for_lane(manifest_data, "candidate")
    lane_cfg = candidate_lane.get("lane", {})
    policy = manifest_data.get("promotion_policy", {})
    criteria = policy.get("criteria", {})
    lane_rules = manifest_data.get("lane_rules", {}).get("candidate", {})

    trace_window = criteria.get("trace_window_days")
    window_days: int | None = None
    try:
        window_days = int(trace_window) if trace_window is not None else None
    except (TypeError, ValueError):
        window_days = None
    summary = summarize_candidate_activity(manager_trace, "candidate", window_days)
    stats = summary["stats"]
    lane_verdict, verdict_reasons = verdict(stats, criteria)
    stage5_commits = summarize_stage5_commits(stage5_trace)

    print(f"Manifest: {manifest_path} (version={manifest.version})")
    print(f"Candidate lane label: {lane_cfg.get('label')} ({lane_cfg.get('status')})")
    print(f"Stage version: {candidate_lane.get('stage_version_name')} ({candidate_lane.get('stage')})")
    print(f"Manager version: {candidate_lane.get('manager_version_name')}")
    print(f"RAG version: {candidate_lane.get('rag_version_name')}")
    trace_window = criteria.get("trace_window_days")
    print(f"Required regression pack: {lane_cfg.get('regression_pack')}")
    print("--- Promotion policy criteria ---")
    print(f"  Success threshold: {criteria.get('candidate_success_threshold', 0)}")
    print(f"  Failure budget: {criteria.get('candidate_failure_budget', 0)}")
    window_label = f" (last {window_days} days)" if window_days else ""
    print(f"  Trace window days: {trace_window if trace_window is not None else 'N/A'}")
    print("--- Candidate lane rules ---")
    if lane_rules:
        for rule_key, rule_value in lane_rules.items():
            print(f"  {rule_key}: {rule_value}")
    else:
        print("  (no explicit lane rules provided)")
    print("--- Candidate telemetry ---")
    print(
        f"  Real candidate successes: {stats['real_successes']}  failures: {stats['real_failures']}{window_label}"
    )
    print(
        f"  Guard/regression successes: {stats['guard_successes']}  failures: {stats['guard_failures']}"
    )
    print(f"  Required successes: {criteria.get('candidate_success_threshold', 0)}")
    print(f"  Failure budget: {criteria.get('candidate_failure_budget', 0)}")
    print("--- Recent candidate jobs ---")
    if summary["recent"]:
        for item in summary["recent"]:
            print(f"  {item['timestamp']} :: stage={item['stage']} target={item['target']} rc={item['return_code']}")
    else:
        print("  No candidate jobs logged yet.")
    print("--- Recent stage5 commits ---")
    if stage5_commits:
        for commit in stage5_commits:
            print(
                f"  {commit['timestamp']} :: {commit['job_id']} targets={commit['targets']} "
                f"Δ+{commit['total_added']}/-{commit['total_deleted']}"
            )
    else:
        print("  No Stage-5 manager commits recorded.")

    missing_evidence = list(verdict_reasons)
    if not stage5_commits:
        missing_evidence.append("No Stage-5 commits recorded.")
    print("--- Verdict ---")
    if lane_verdict == "promotable":
        print("PROMOTABLE: candidate lane meets success/failure thresholds.")
        if missing_evidence:
            print(" Additional evidence recommended: " + "; ".join(missing_evidence))
    else:
        detail = "; ".join(missing_evidence) if missing_evidence else "missing evidence."
        if window_days:
            detail = f"{detail} (evaluated over last {window_days} days)"
        print(f"NOT READY: {detail}")
    last_decision = policy.get("last_decision", {})
    print(f"Last recorded promotion decision: {last_decision.get('status')} on {last_decision.get('date')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
