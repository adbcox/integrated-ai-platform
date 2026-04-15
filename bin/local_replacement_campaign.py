#!/usr/bin/env python3
"""Local-first replacement campaign scaffold for bounded complex tasks."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from codex51_attribution import (
    aggregate_attribution,
    enrich_run_row,
    load_jsonl,
    write_attribution_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "config" / "local_first_campaign.json"
STAGE7_MANAGER = REPO_ROOT / "bin" / "stage7_manager.py"
PLAN_DIR = REPO_ROOT / "artifacts" / "manager6" / "plans"
RUN_ROOT = REPO_ROOT / "artifacts" / "codex51" / "campaign"
RUNS_JSONL = RUN_ROOT / "runs.jsonl"
ATTRIBUTION_REPORT_PATH = REPO_ROOT / "artifacts" / "codex51" / "attribution" / "latest.json"


@dataclass
class CampaignTask:
    task_id: str
    title: str
    in_scope: bool
    task_class: str
    query: str
    notes: str


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_tasks(config: dict[str, Any]) -> list[CampaignTask]:
    tasks: list[CampaignTask] = []
    for row in config.get("tasks", []):
        if not isinstance(row, dict):
            continue
        task_id = str(row.get("task_id") or "")
        if not task_id:
            continue
        tasks.append(
            CampaignTask(
                task_id=task_id,
                title=str(row.get("title") or task_id),
                in_scope=bool(row.get("in_scope", True)),
                task_class=str(row.get("task_class") or "unknown"),
                query=str(row.get("query") or ""),
                notes=str(row.get("notes") or ""),
            )
        )
    return tasks


def _profile_args(profile: str) -> list[str]:
    if profile == "normal":
        return []
    if profile == "first_attempt_only":
        return ["--subplan-failure-policy", "abort", "--family-rescue-budget", "0"]
    if profile == "manager_reduced":
        return [
            "--subplan-failure-policy",
            "abort",
            "--family-rescue-budget",
            "0",
            "--manager-history-window-days",
            "1",
            "--manager-memory-window-days",
            "1",
        ]
    if profile == "rag_reduced":
        return [
            "--rag-max-targets",
            "3",
            "--related-limit",
            "0",
            "--history-window",
            "3",
            "--max-subplans",
            "1",
            "--subplan-size",
            "1",
        ]
    raise ValueError(f"unsupported profile: {profile}")


def _load_plan_result(plan_id: str) -> dict[str, Any]:
    plan_path = PLAN_DIR / f"{plan_id}.json"
    if not plan_path.exists():
        return {"error": "plan_history_missing", "plan_path": str(plan_path)}
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    history = payload.get("history") or []
    finished = None
    for row in reversed(history):
        if str(row.get("event_type") or "") == "attempt_finished":
            finished = row
            break
    if not isinstance(finished, dict):
        return {"error": "attempt_finished_missing", "plan_path": str(plan_path)}
    statuses = [row for row in (finished.get("statuses") or []) if isinstance(row, dict)]
    plan_payload = finished.get("plan_payload") or payload.get("plan_payload") or {}
    expected_subplans = [row for row in (plan_payload.get("subplans") or []) if isinstance(row, dict)]
    expected_ids = {str(row.get("subplan_id") or "") for row in expected_subplans if str(row.get("subplan_id") or "")}
    base_rows = [row for row in statuses if str(row.get("subplan_id") or "") in expected_ids]
    first_attempt_success = sum(1 for row in base_rows if str(row.get("status") or "") in {"success", "resumed_skip_completed"})
    first_attempt_rate = round(first_attempt_success / len(expected_ids), 3) if expected_ids else 0.0
    rescue_count = sum(
        1
        for row in statuses
        if str(row.get("strategy") or "") == "split_subplan"
        or bool(row.get("retry"))
        or str(row.get("retry_strategy") or "")
    ) + len([x for x in (plan_payload.get("recoveries") or []) if isinstance(x, dict)])
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
    )
    return {
        "plan_path": str(plan_path),
        "state": str(finished.get("state") or ""),
        "failure_code": int(finished.get("failure_code") or 0),
        "ranking_version": str((plan_payload.get("provenance") or {}).get("ranking_version") or ""),
        "first_attempt_quality_rate": first_attempt_rate,
        "rescue_count": rescue_count,
        "escalation_count": escalation_count,
        "guard_count": guard_count,
        "status_count": len(statuses),
        "stage_reconciliation": plan_payload.get("stage_reconciliation"),
        "plan_payload": plan_payload,
        "statuses": statuses,
    }


def _append_run(row: dict[str, Any]) -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    with RUNS_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _refresh_attribution_report() -> dict[str, Any]:
    rows = load_jsonl(RUNS_JSONL)
    summary = aggregate_attribution(rows)
    report = {
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "campaign_runs_path": str(RUNS_JSONL),
            "row_count": len(rows),
        },
        "campaign_aggregate": summary,
    }
    write_attribution_report(ATTRIBUTION_REPORT_PATH, report)
    return report


def run_task(
    *,
    task: CampaignTask,
    lane: str,
    profile: str,
    dry_run: bool,
    extra_args: list[str],
) -> dict[str, Any]:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    plan_id = f"{task.task_id}-{profile}-{ts}"
    cmd = [
        sys.executable,
        str(STAGE7_MANAGER),
        "--plan-id",
        plan_id,
        "--commit-msg",
        f"campaign:{task.task_id}:{profile}",
        "--query",
        *task.query.split(),
        "--max-subplans",
        "2",
        "--subplan-size",
        "2",
        "--plan-status",
        "campaign",
    ]
    cmd.extend(_profile_args(profile))
    cmd.extend(extra_args)
    if dry_run:
        cmd.append("--dry-run")

    started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    proc = subprocess.run(cmd, cwd=REPO_ROOT)
    finished = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = _load_plan_result(plan_id)
    success = proc.returncode == 0 and int(result.get("failure_code", 1)) == 0
    attribution_primary = "mixed_gain"
    if success and result.get("first_attempt_quality_rate", 0.0) >= 1.0 and int(result.get("rescue_count", 0)) == 0:
        attribution_primary = "model_gain"
    elif success and int(result.get("rescue_count", 0)) > 0:
        attribution_primary = "manager_gain"
    elif success and str(result.get("ranking_version") or "").startswith("rag9"):
        attribution_primary = "retrieval_gain"
    elif int(result.get("guard_count", 0)) > 0:
        attribution_primary = "guard_policy_gain"

    row = {
        "campaign_run_id": f"{task.task_id}:{profile}:{ts}",
        "timestamp_utc": finished,
        "started_at_utc": started,
        "task_id": task.task_id,
        "task_title": task.title,
        "task_class": task.task_class,
        "in_scope": task.in_scope,
        "lane": lane,
        "attribution_profile": profile,
        "dry_run": dry_run,
        "plan_id": plan_id,
        "command": " ".join(shlex.quote(part) for part in cmd),
        "return_code": proc.returncode,
        "success": success,
        "outcome": "success" if success else "failure",
        "rescue_count": int(result.get("rescue_count", 0)),
        "escalation_count": int(result.get("escalation_count", 0)),
        "guard_count": int(result.get("guard_count", 0)),
        "first_attempt_quality_rate": float(result.get("first_attempt_quality_rate", 0.0)),
        "ranking_version": str(result.get("ranking_version") or ""),
        "stage_reconciliation_present": bool(result.get("stage_reconciliation")),
        "attribution_primary": attribution_primary,
        "plan_result": result,
    }
    row = enrich_run_row(
        row=row,
        repo_root=REPO_ROOT,
        plan_payload=result.get("plan_payload") if isinstance(result.get("plan_payload"), dict) else {},
        statuses=result.get("statuses") if isinstance(result.get("statuses"), list) else [],
    )
    if isinstance(row.get("plan_result"), dict):
        row["plan_result"] = {
            k: v
            for k, v in row["plan_result"].items()
            if k not in {"plan_payload", "statuses"}
        }
    _append_run(row)
    (RUN_ROOT / f"{plan_id}.json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local-first replacement campaign scaffold")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List configured in-scope campaign tasks")

    run = sub.add_parser("run", help="Run one campaign task through stage7 local path")
    run.add_argument("--task-id", required=True)
    run.add_argument("--profile", default="normal", choices=["normal", "first_attempt_only", "manager_reduced", "rag_reduced"])
    run.add_argument("--lane", default="stage7")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--no-dry-run", action="store_true")
    run.add_argument("--extra-arg", action="append", default=[], help="extra arg passed to stage7_manager")

    batch = sub.add_parser("run-batch", help="Run all in-scope tasks")
    batch.add_argument("--profile", default="normal", choices=["normal", "first_attempt_only", "manager_reduced", "rag_reduced"])
    batch.add_argument("--lane", default="stage7")
    batch.add_argument("--dry-run", action="store_true")
    batch.add_argument("--no-dry-run", action="store_true")
    batch.add_argument("--extra-arg", action="append", default=[], help="extra arg passed to stage7_manager")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config).resolve())
    tasks = parse_tasks(config)
    default_dry_run = bool(config.get("default_dry_run", True))

    if args.command == "list":
        rows = [
            {
                "task_id": t.task_id,
                "title": t.title,
                "task_class": t.task_class,
                "in_scope": t.in_scope,
                "query": t.query,
            }
            for t in tasks
        ]
        print(json.dumps({"tasks": rows}, ensure_ascii=False, indent=2))
        return 0

    dry_run = default_dry_run
    if getattr(args, "dry_run", False):
        dry_run = True
    if getattr(args, "no_dry_run", False):
        dry_run = False
    extra_args = [str(x) for x in getattr(args, "extra_arg", []) if str(x)]

    if args.command == "run":
        target = next((t for t in tasks if t.task_id == args.task_id), None)
        if target is None:
            print(f"unknown task-id: {args.task_id}", file=sys.stderr)
            return 2
        row = run_task(task=target, lane=args.lane, profile=args.profile, dry_run=dry_run, extra_args=extra_args)
        attribution_report = _refresh_attribution_report()
        row["attribution_report_path"] = str(ATTRIBUTION_REPORT_PATH)
        row["attribution_summary"] = attribution_report.get("campaign_aggregate", {})
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0 if row["return_code"] == 0 else row["return_code"]

    if args.command == "run-batch":
        rc = 0
        rows: list[dict[str, Any]] = []
        for task in tasks:
            if not task.in_scope:
                continue
            row = run_task(task=task, lane=args.lane, profile=args.profile, dry_run=dry_run, extra_args=extra_args)
            rows.append(row)
            if int(row["return_code"]) != 0:
                rc = int(row["return_code"])
        attribution_report = _refresh_attribution_report()
        print(
            json.dumps(
                {
                    "runs": rows,
                    "attribution_report_path": str(ATTRIBUTION_REPORT_PATH),
                    "attribution_summary": attribution_report.get("campaign_aggregate", {}),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
