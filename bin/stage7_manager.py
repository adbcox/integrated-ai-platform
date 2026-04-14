#!/usr/bin/env python3
"""Manager-6 orchestrator for Stage-7 multi-plan execution."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
from promotion.tracing import PromotionTraceEntry, append_trace, current_commit_hash

STAGE6_MANAGER = REPO_ROOT / "bin" / "stage6_manager.py"
STAGE_RAG6_PLAN = REPO_ROOT / "bin" / "stage_rag6_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "manager6"


def plan_history_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / f"{plan_id}.json"


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


def _write_stage6_jobs_file(targets: list[str]) -> Path:
    payload = [{"path": path, "source": "stage7-subplan"} for path in targets]
    file_path = Path(tempfile.mkstemp(prefix="stage7-subplan-", suffix=".json")[1])
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def run_stage6_subplan(
    *,
    subplan: dict[str, Any],
    args: argparse.Namespace,
    env: dict[str, str],
    op_index: int,
) -> dict[str, Any]:
    subplan_id = str(subplan.get("subplan_id") or f"subplan-{op_index + 1}")
    targets = [str(t) for t in subplan.get("targets", []) if t]
    jobs_file = _write_stage6_jobs_file(targets)
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
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    proc = subprocess.run(cmd, env={**os.environ, **env})
    jobs_file.unlink(missing_ok=True)
    status = {
        "subplan_id": subplan_id,
        "targets": targets,
        "status": "success" if proc.returncode == 0 else "failure",
        "return_code": proc.returncode,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "grouped_subplan",
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
        status["retry"] = True
        status["retry_strategy"] = "split_on_failure"
        status["refinement_of_subplan"] = failed_subplan.get("subplan_id")
        split_statuses.append(status)
        if status["return_code"] != 0:
            all_success = False
    return all_success, split_statuses


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

    rag6_plan = run_stage_rag6(args)
    subplans = list(rag6_plan.get("subplans", []))

    plan_payload = {
        "plan_id": args.plan_id,
        "query": " ".join(args.query),
        "notes": args.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "subplans": subplans,
        "provenance": rag6_plan.get("provenance", {}),
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
    statuses: list[dict[str, Any]] = []
    exit_code = 0

    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_started",
            "state": "running",
            "plan_payload": plan_payload,
            "statuses": [],
        },
    )

    for idx, subplan in enumerate(subplans):
        status = run_stage6_subplan(subplan=subplan, args=args, env=env, op_index=idx)
        statuses.append(status)
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
            statuses.extend(split_statuses)
            plan_payload.setdefault("recoveries", []).append(
                {
                    "failed_subplan": status["subplan_id"],
                    "strategy": "split_on_failure",
                    "split_count": len(split_statuses),
                    "result": "success" if split_success else "partial_or_failed",
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

    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_finished",
            "state": final_state,
            "statuses": statuses,
            "failure_code": exit_code,
            "plan_payload": plan_payload,
        },
    )

    lane_cfg = versions.get("lane", {})
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
        extra={"plan_id": args.plan_id, "subplans": statuses, "plan_payload": plan_payload},
    )
    append_trace(trace, trace_dir=TRACE_DIR)

    if exit_code == 0:
        print(f"[stage7] orchestrated {len(statuses)} subplan execution(s) for plan {args.plan_id}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
