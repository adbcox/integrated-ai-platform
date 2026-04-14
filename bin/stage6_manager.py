#!/usr/bin/env python3
"""Manager-5 orchestrator for Stage-6 multi-target batches."""

# STAGE6_PLACEHOLDER

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
from promotion.tracing import PromotionTraceEntry, append_trace, current_commit_hash

STAGE5_MANAGER = REPO_ROOT / "bin" / "stage5_manager.py"
STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "manager5"
PLACEHOLDER_LITERAL = "# STAGE6_PLACEHOLDER"


@dataclass
class Stage6Job:
    path: str
    notes: str | None = None
    lines: str | None = None
    source: str | None = None


def plan_history_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / f"{plan_id}.json"


def write_plan_history(plan_id: str, payload: dict[str, Any]) -> None:
    history_path = plan_history_path(plan_id)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_stage_rag4(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(STAGE_RAG4_PLAN),
        "--plan-id",
        args.plan_id,
        "--top",
        str(args.top),
        "--window",
        str(args.window),
        "--preview-lines",
        str(args.preview_lines),
        "--related-limit",
        str(args.related_limit),
        "--history-window",
        str(args.history_window),
    ]
    if args.notes:
        cmd.extend(["--notes", args.notes])
    cmd.extend(args.query)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def load_jobs_from_file(path: Path) -> list[Stage6Job]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("jobs file must be a JSON array")
    jobs: list[Stage6Job] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        path_value = entry.get("path")
        if not path_value:
            continue
        jobs.append(
            Stage6Job(
                path=path_value,
                notes=entry.get("notes"),
                lines=entry.get("lines"),
                source=entry.get("source"),
            )
        )
    return jobs


def plan_to_jobs(
    plan: dict[str, Any],
    allowed: list[str],
    max_entries: int,
    min_confidence: int,
) -> list[Stage6Job]:
    jobs: list[Stage6Job] = []
    for target in plan.get("targets", [])[: max_entries]:
        path = target.get("path")
        if not path:
            continue
        if allowed and not any(path.startswith(prefix) for prefix in allowed):
            continue
        confidence = target.get("confidence", 0)
        if confidence < min_confidence:
            continue
        jobs.append(
            Stage6Job(
                path=path,
                notes=plan.get("notes"),
                lines=None,
                source=target.get("source"),
            )
        )
    return jobs


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
    allowed = lane_cfg.get("allowed_targets", [])
    if allowed:
        env["PROMOTION_ALLOWED_TARGETS"] = ",".join(allowed)
    return env


def create_stage5_batch(job: Stage6Job, args: argparse.Namespace) -> Path:
    literal_old = args.literal_old
    literal_new = args.literal_new
    payload = {
        "query": " ".join(args.query),
        "target": job.path,
        "message": args.message_template.format(
            path=job.path,
            source=(job.source or "rag4"),
            old=literal_old,
            new=literal_new,
        ),
        "lines": job.lines or args.lines,
    }
    if args.notes:
        payload["notes"] = args.notes
    if args.max_total_lines:
        payload["max_total_lines"] = args.max_total_lines
    batch_path = Path(tempfile.mkstemp(prefix="stage6-", suffix=".json")[1])
    batch_path.write_text(json.dumps([payload], ensure_ascii=False, indent=2), encoding="utf-8")
    return batch_path


def run_stage5_job(job: Stage6Job, args: argparse.Namespace, env: dict[str, str], idx: int) -> int:
    batch_path = create_stage5_batch(job, args)
    commit_msg = f"{args.commit_msg} - stage6 op {idx + 1}"
    if args.dry_run:
        print(f"[stage6] dry-run planning job {idx + 1}: target={job.path}, commit='{commit_msg}'")
        batch_path.unlink(missing_ok=True)
        return 0
    cmd = [
        sys.executable,
        str(STAGE5_MANAGER),
        "--batch-file",
        str(batch_path),
        "--commit-msg",
        commit_msg,
        "--max-ops",
        str(args.max_ops),
        "--max-total-lines",
        str(args.max_total_lines),
    ]
    if args.manifest:
        cmd.extend(["--manifest", args.manifest])
    proc = subprocess.run(cmd, env={**os.environ, **env})
    batch_path.unlink(missing_ok=True)
    return proc.returncode


def record_trace(
    lane: str,
    lane_cfg: dict[str, Any],
    versions: dict[str, Any],
    manifest_version: int,
    manifest_path: Path,
    args: argparse.Namespace,
    statuses: list[dict[str, Any]],
    plan_id: str,
    plan_payload: dict[str, Any],
    return_code: int,
    trace_dir: Path,
) -> None:
    entry = PromotionTraceEntry(
        lane=lane,
        lane_label=lane_cfg.get("label", "Stage-6 preview"),
        lane_status=lane_cfg.get("status", "preview"),
        lane_reason=f"plan:{plan_id}",
        stage=versions.get("stage"),
        stage_version=versions.get("stage_version_name"),
        manager_version=versions.get("manager_version_name"),
        rag_version=versions.get("rag_version_name"),
        promotion_policy_status=args.plan_status,
        manifest_version=manifest_version,
        manifest_path=str(manifest_path),
        literal_lines=0,
        return_code=return_code,
        promotion_outcome="success" if return_code == 0 else "failure",
        commit_hash=current_commit_hash(),
        extra={"plan_id": plan_id, "jobs": statuses, "plan_payload": plan_payload},
    )
    append_trace(entry, trace_dir=trace_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage-6 multi-target manager")
    parser.add_argument("--query", nargs="+", required=True, help="Natural language query for Stage-6")
    parser.add_argument("--plan-id", required=True, help="Identifier used across Stage-6 planning")
    parser.add_argument("--commit-msg", required=True, help="Commit message prefix for generated stage5 commits")
    parser.add_argument("--notes", default="", help="General notes for the Stage-6 batch")
    parser.add_argument("--lines", default="auto", help="Line range hint for all Stage-6 jobs")
    parser.add_argument("--max-ops", type=int, default=3, help="Per-stage5 invocation maximum operations")
    parser.add_argument("--max-total-lines", type=int, default=80, help="Aggregate diff budget per stage5 job")
    parser.add_argument("--top", type=int, default=5, help="RAG-4 top hits to consider")
    parser.add_argument("--window", type=int, default=25, help="RAG-4 search window")
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--max-entries", type=int, default=3, help="Max Stage-6 entries to orchestrate")
    parser.add_argument("--jobs-file", help="Optional manual JSON jobs definition")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH), help="Promotion manifest path")
    parser.add_argument(
        "--message-template",
        default="replace exact text '{old}' with '{new}' for {path} (source={source})",
        help="Worker instruction message template",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without invoking Stage-5 manager")
    parser.add_argument("--plan-status", default="preview", help="Optional status used in trace entries")
    parser.add_argument("--fallback-target", help="Fallback target when RAG-4 returns no eligible jobs")
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument("--history-window", type=int, default=15, help="Git history window for Stage RAG-4")
    parser.add_argument("--min-confidence", type=int, default=1, help="Minimum RAG-4 confidence before enqueuing a target")
    parser.add_argument("--literal-old", default=PLACEHOLDER_LITERAL, help="Literal old text for Stage-4 replacements")
    parser.add_argument("--literal-new", default=f"{PLACEHOLDER_LITERAL} (updated)", help="Literal new text for Stage-4 replacements")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest_cfg = load_manifest(manifest_path)
    lane_name = "stage6"
    versions = resolve_versions_for_lane(manifest_cfg.data, lane_name)
    lane_cfg = versions.get("lane", {})
    allowed_targets = lane_cfg.get("allowed_targets", ["bin/"])

    plan_payload: dict[str, Any] = {}
    if args.jobs_file:
        jobs = load_jobs_from_file(Path(args.jobs_file))
        plan_payload = {
            "plan_id": args.plan_id,
            "query": " ".join(args.query),
            "notes": args.notes,
        "targets": [job.path for job in jobs],
        "created_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        plan = run_stage_rag4(args)
        jobs = plan_to_jobs(plan, allowed_targets, args.max_entries, args.min_confidence)
        args.plan_details = plan
        if not jobs and args.fallback_target:
            fallback_path = args.fallback_target
            if allowed_targets and not any(fallback_path.startswith(prefix) for prefix in allowed_targets):
                raise SystemExit(f"[stage6] fallback target {fallback_path} is not allowed for the lane")
            jobs = [Stage6Job(path=fallback_path, source="fallback")]
            plan.setdefault("targets", []).append({"path": fallback_path, "source": "fallback"})
        plan_payload = {
            "plan_id": args.plan_id,
            "query": " ".join(args.query),
            "notes": args.notes,
            "targets": [job.path for job in jobs],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    if not jobs:
        print("[stage6] no eligible jobs found, nothing to run")
        return 0

    env = build_promotion_env(lane_name, versions, manifest_cfg.version, manifest_path)
    statuses: list[dict[str, Any]] = []
    exit_code = 0
    for idx, job in enumerate(jobs):
        code = run_stage5_job(job, args, env, idx)
        statuses.append({"target": job.path, "status": "success" if code == 0 else "failure"})
        if code != 0:
            exit_code = code
            break

    if exit_code != 0 and args.fallback_target and not any(job.source == "fallback" for job in jobs):
        print(f"[stage6] retrying plan {args.plan_id} with fallback target {args.fallback_target}")
        retry_job = Stage6Job(path=args.fallback_target, source="fallback")
        retry_code = run_stage5_job(retry_job, args, env, len(statuses))
        statuses.append({"target": retry_job.path, "status": "success" if retry_code == 0 else "failure", "retry": True})
        exit_code = retry_code
        plan_payload.setdefault("retries", []).append({"target": retry_job.path, "status": "pending" if retry_code != 0 else "success"})
        plan_payload["notes"] = plan_payload.get("notes") or "fallback retry"

    history_record = {
        "plan_id": args.plan_id,
        "plan_payload": plan_payload,
        "statuses": statuses,
        "failure_code": exit_code,
    }
    write_plan_history(args.plan_id, history_record)

    record_trace(
        lane=lane_name,
        lane_cfg=lane_cfg,
        versions=versions,
        manifest_version=manifest_cfg.version,
        manifest_path=manifest_path,
        args=args,
        statuses=statuses,
        plan_id=args.plan_id,
        plan_payload=plan_payload,
        return_code=exit_code,
        trace_dir=TRACE_DIR,
    )
    if exit_code == 0:
        print(f"[stage6] orchestrated {len(statuses)} job(s) for plan {args.plan_id}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
