#!/usr/bin/env python3
"""Manager-5 orchestrator for Stage-6 multi-target batches."""

# STAGE6_PLACEHOLDER

from __future__ import annotations

import argparse
import json
import os
import re
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
from promotion.failure_memory import assess_target_risk
from promotion.tracing import PromotionTraceEntry, append_trace, current_commit_hash

STAGE5_MANAGER = REPO_ROOT / "bin" / "stage5_manager.py"
STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "manager5"
STAGE5_TRACE_FILE = REPO_ROOT / "artifacts" / "stage5_manager" / "traces.jsonl"
# STAGE6_PLACEHOLDER (updated)
# STAGE6_PLACEHOLDER (updated)
# STAGE6_PLACEHOLDER (updated)
PLACEHOLDER_LITERAL = "# STAGE6_PLACEHOLDER\n# STAGE6_PLACEHOLDER\n# STAGE6_PLACEHOLDER"
PLACEHOLDER_LITERAL_UPDATED = "# STAGE6_PLACEHOLDER (updated)\n# STAGE6_PLACEHOLDER (updated)\n# STAGE6_PLACEHOLDER (updated)"
PLACEHOLDER_BLOCK_RE = re.compile(
    r"(?m)^# STAGE6_PLACEHOLDER(?:[^\n]*)\n# STAGE6_PLACEHOLDER(?:[^\n]*)\n# STAGE6_PLACEHOLDER(?:[^\n]*)"
)


@dataclass
class Stage6Job:
    path: str
    notes: str | None = None
    lines: str | None = None
    source: str | None = None
    refinement_of: str | None = None
    literal_old: str | None = None
    literal_new: str | None = None
    sync_reason: str | None = None
    message: str | None = None


LINK_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")
GENERIC_LINK_TOKENS = {
    "bin",
    "docs",
    "file",
    "files",
    "path",
    "target",
    "targets",
    "lane",
    "stage",
    "py",
    "sh",
}


def plan_history_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / f"{plan_id}.json"


def load_plan_history(plan_id: str) -> dict[str, Any]:
    history_path = plan_history_path(plan_id)
    if not history_path.exists():
        return {}
    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


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
    event.setdefault("event_type", "update")
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    history.append(event)
    plan_payload: dict[str, Any] = existing.get("plan_payload", {})
    plan_payload.update(payload.get("plan_payload", {}))
    current_state = payload.get("state") or existing.get("current_state")
    latest_statuses = payload.get("statuses") or existing.get("latest_statuses", [])
    attempts = int(existing.get("attempt_count", 0))
    if payload.get("event_type") == "attempt_started":
        attempts += 1
    merged = {
        "plan_id": plan_id,
        "plan_payload": plan_payload,
        "history": history,
        "current_state": current_state,
        "latest_statuses": latest_statuses,
        "attempt_count": attempts,
        "last_updated": payload.get("timestamp"),
    }
    history_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_jsonl_slice(path: Path, start_line: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            if idx < start_line:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as fh:
        return sum(1 for _ in fh)


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
        "--max-targets",
        str(args.rag_max_targets),
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
) -> tuple[list[Stage6Job], dict[str, Any]]:
    def _path_tokens(path: str) -> set[str]:
        parts: list[str] = []
        for segment in path.lower().replace("/", "_").split("_"):
            if not segment:
                continue
            parts.extend(LINK_TOKEN_SPLIT_RE.split(segment))
        tokens: set[str] = set()
        for token in parts:
            token = token.strip()
            if not token or token in GENERIC_LINK_TOKENS:
                continue
            tokens.add(token)
            alpha = re.sub(r"\d+", "", token)
            if alpha and alpha != token and alpha not in GENERIC_LINK_TOKENS:
                tokens.add(alpha)
        return tokens

    def _query_tokens(plan_payload: dict[str, Any]) -> set[str]:
        raw_tokens = plan_payload.get("provenance", {}).get("query_tokens", [])
        if not isinstance(raw_tokens, list):
            return set()
        tokens: set[str] = set()
        for token in raw_tokens:
            value = str(token).lower().strip()
            if not value:
                continue
            for split in LINK_TOKEN_SPLIT_RE.split(value):
                split = split.strip()
                if not split or split in GENERIC_LINK_TOKENS:
                    continue
                tokens.add(split)
        return tokens

    def _secondary_link_evidence(
        *,
        candidate: dict[str, Any],
        primary: dict[str, Any],
        query_tokens: set[str],
    ) -> tuple[float, list[str], bool]:
        evidence: list[str] = []
        score = 0.0

        candidate_path = str(candidate.get("path") or "")
        primary_path = str(primary.get("path") or "")
        candidate_related = {str(p) for p in (candidate.get("related") or []) if p}
        primary_related = {str(p) for p in (primary.get("related") or []) if p}
        direct_related = candidate_path in primary_related or primary_path in candidate_related
        if direct_related:
            score += 3.0
            evidence.append("direct_related")

        candidate_tokens = _path_tokens(candidate_path)
        primary_tokens = _path_tokens(primary_path)
        token_overlap = (candidate_tokens & query_tokens)
        if token_overlap:
            score += min(1.5, 0.75 * len(token_overlap))
            evidence.append(f"query_token_overlap:{','.join(sorted(token_overlap))}")

        family_overlap = (candidate_tokens & primary_tokens)
        if family_overlap:
            score += 0.75
            evidence.append(f"path_family_overlap:{','.join(sorted(list(family_overlap)[:2]))}")

        candidate_conf = float(candidate.get("confidence") or 0)
        primary_score = float(primary.get("rank_score") or 0.0)
        candidate_score = float(candidate.get("rank_score") or 0.0)
        if candidate_conf >= 6 and primary_score > 0 and candidate_score >= (primary_score * 0.68):
            score += 0.75
            evidence.append("high_confidence_proximal")

        return score, evidence, direct_related

    jobs: list[Stage6Job] = []
    selection: dict[str, Any] = {"selected": [], "dropped": []}
    eligible_targets: list[dict[str, Any]] = []
    for target in plan.get("targets", []):
        path = target.get("path")
        if not path:
            selection["dropped"].append({"path": None, "reason": "missing_path"})
            continue
        if allowed and not any(path.startswith(prefix) for prefix in allowed):
            selection["dropped"].append({"path": path, "reason": "target_not_allowed"})
            continue
        confidence = target.get("confidence", 0)
        if confidence < min_confidence:
            selection["dropped"].append({"path": path, "reason": "below_confidence", "confidence": confidence})
            continue
        eligible_targets.append(target)

    if not eligible_targets:
        return jobs, selection

    # Keep the strongest target as primary, then only allow linked secondary jobs.
    primary = eligible_targets[0]
    primary_path = str(primary.get("path"))
    selected_paths: set[str] = set()
    query_tokens = _query_tokens(plan)

    jobs.append(
        Stage6Job(
            path=primary_path,
            notes=plan.get("notes"),
            lines=None,
            source=primary.get("source"),
        )
    )
    selected_paths.add(primary_path)
    selection["selected"].append({"path": primary_path, "reason": "primary"})

    for target in eligible_targets[1:]:
        if len(jobs) >= max_entries:
            selection["dropped"].append({"path": target.get("path"), "reason": "max_entries_reached"})
            continue

        path = str(target.get("path"))
        if path in selected_paths:
            selection["dropped"].append({"path": path, "reason": "duplicate_path"})
            continue

        link_score, link_evidence, direct_related = _secondary_link_evidence(
            candidate=target,
            primary=primary,
            query_tokens=query_tokens,
        )
        keep_secondary = direct_related or link_score >= 1.5
        if not keep_secondary:
            selection["dropped"].append(
                {
                    "path": path,
                    "reason": "unlinked_secondary",
                    "link_score": round(link_score, 2),
                    "link_evidence": link_evidence,
                }
            )
            continue

        jobs.append(
            Stage6Job(
                path=path,
                notes=plan.get("notes"),
                lines=None,
                source=target.get("source"),
            )
        )
        selected_paths.add(path)
        selection["selected"].append(
            {
                "path": path,
                "reason": "linked_secondary" if direct_related else "scored_secondary",
                "linked_to_primary": direct_related,
                "link_score": round(link_score, 2),
                "link_evidence": link_evidence,
            }
        )
    return jobs, selection


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


def _synchronize_literal_pair(target_contents: str, literal_old: str, literal_new: str) -> tuple[str, str, str | None]:
    if not target_contents:
        return literal_old, literal_new, None
    if literal_old in target_contents:
        return literal_old, literal_new, None
    if literal_new in target_contents:
        return literal_new, literal_old, "swap_on_new_match"

    # If neither literal is present, attempt to anchor on the live placeholder block.
    # This keeps fallback resilient after prior candidate edits introduced a new variant.
    match = PLACEHOLDER_BLOCK_RE.search(target_contents)
    if not match:
        return literal_old, literal_new, None

    live_old = match.group(0)
    if live_old == literal_new:
        return literal_new, literal_old, "swap_on_live_match"
    if live_old == literal_old:
        return literal_old, literal_new, None
    return live_old, literal_new, "sync_live_block"


def _single_line_import_base(value: str) -> str | None:
    if "\n" in value:
        return None
    text = value.strip()
    if not text:
        return None
    comment_idx = text.find("#")
    if comment_idx != -1:
        text = text[:comment_idx].rstrip()
    if text.startswith("import ") or text.startswith("from "):
        return text
    return None


def _sync_import_literal_pair(
    target_contents: str,
    literal_old: str,
    literal_new: str,
) -> tuple[str, str] | None:
    """Adapt import/from literals per-target when only inline comments differ."""
    base_old = _single_line_import_base(literal_old)
    base_new = _single_line_import_base(literal_new)
    if not base_old or not base_new or base_old != base_new:
        return None

    lines = target_contents.splitlines()
    candidate_old: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(base_old):
            candidate_old = stripped
            break
    if not candidate_old:
        return None

    desired = literal_new.strip()
    if not desired.startswith(base_old):
        return None
    suffix = desired[len(base_old) :]
    candidate_new = f"{base_old}{suffix}".rstrip()
    return candidate_old, candidate_new


def create_stage5_batch(job: Stage6Job, args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    literal_old = job.literal_old or args.literal_old
    literal_new = job.literal_new or args.literal_new
    target_path = (REPO_ROOT / job.path).resolve()
    try:
        target_contents = target_path.read_text(encoding="utf-8")
    except OSError:
        target_contents = ""

    literal_old, literal_new, sync_reason = _synchronize_literal_pair(
        target_contents=target_contents,
        literal_old=literal_old,
        literal_new=literal_new,
    )
    if sync_reason is None and literal_old not in target_contents:
        import_sync = _sync_import_literal_pair(
            target_contents=target_contents,
            literal_old=args.literal_old,
            literal_new=args.literal_new,
        )
        if import_sync:
            literal_old, literal_new = import_sync
            sync_reason = "sync_import_line"

    message = job.message or args.message_template.format(
        path=job.path,
        source=(job.source or "rag4"),
        old=literal_old,
        new=literal_new,
    )
    payload = {
        "query": " ".join(args.query),
        "target": job.path,
        "message": message,
        "lines": job.lines or args.lines,
    }
    if args.min_lines:
        payload["min_lines"] = args.min_lines
    if args.notes:
        payload["notes"] = args.notes
    if args.max_total_lines:
        payload["max_total_lines"] = args.max_total_lines
    batch_path = Path(tempfile.mkstemp(prefix="stage6-", suffix=".json")[1])
    batch_path.write_text(json.dumps([payload], ensure_ascii=False, indent=2), encoding="utf-8")
    return batch_path, {
        "literal_old": literal_old,
        "literal_new": literal_new,
        "sync_reason": sync_reason,
        "message": message,
    }


def build_job_contracts(jobs: list[Stage6Job], args: argparse.Namespace) -> list[Stage6Job]:
    """Resolve per-target literal/message contracts before Stage-5 dispatch."""
    resolved: list[Stage6Job] = []
    for job in jobs:
        target_path = (REPO_ROOT / job.path).resolve()
        try:
            target_contents = target_path.read_text(encoding="utf-8")
        except OSError:
            target_contents = ""

        literal_old, literal_new, sync_reason = _synchronize_literal_pair(
            target_contents=target_contents,
            literal_old=args.literal_old,
            literal_new=args.literal_new,
        )
        if sync_reason is None and literal_old not in target_contents:
            import_sync = _sync_import_literal_pair(
                target_contents=target_contents,
                literal_old=args.literal_old,
                literal_new=args.literal_new,
            )
            if import_sync:
                literal_old, literal_new = import_sync
                sync_reason = "sync_import_line"

        message = args.message_template.format(
            path=job.path,
            source=(job.source or "rag4"),
            old=literal_old,
            new=literal_new,
        )
        resolved.append(
            Stage6Job(
                path=job.path,
                notes=job.notes,
                lines=job.lines,
                source=job.source,
                refinement_of=job.refinement_of,
                literal_old=literal_old,
                literal_new=literal_new,
                sync_reason=sync_reason,
                message=message,
            )
        )
    return resolved


def run_stage5_job(job: Stage6Job, args: argparse.Namespace, env: dict[str, str], idx: int) -> dict[str, Any]:
    batch_path, literal_info = create_stage5_batch(job, args)
    commit_msg = f"{args.commit_msg} - stage6 op {idx + 1}"
    started_at = datetime.now(timezone.utc).isoformat()
    if args.dry_run:
        print(f"[stage6] dry-run planning job {idx + 1}: target={job.path}, commit='{commit_msg}'")
        batch_path.unlink(missing_ok=True)
        return {
            "target": job.path,
            "status": "planned",
            "return_code": 0,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "source": job.source,
            "refinement_of": job.refinement_of,
            "retry_class": args.retry_class,
            "commit_msg": commit_msg,
            "literal_sync": literal_info,
        }
    trace_line_start = _line_count(STAGE5_TRACE_FILE)
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
    trace_rows = _read_jsonl_slice(STAGE5_TRACE_FILE, trace_line_start)
    latest_trace = trace_rows[-1] if trace_rows else {}
    batch_path.unlink(missing_ok=True)
    return {
        "target": job.path,
        "status": "success" if proc.returncode == 0 else "failure",
        "return_code": proc.returncode,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "source": job.source,
        "refinement_of": job.refinement_of,
        "retry_class": args.retry_class,
        "commit_msg": commit_msg,
        "stage5_job_id": latest_trace.get("job_id"),
        "stage5_commit_hash": latest_trace.get("commit_hash"),
        "stage5_total_added": latest_trace.get("total_added"),
        "stage5_total_deleted": latest_trace.get("total_deleted"),
        "literal_sync": literal_info,
    }


def _build_refinement_job(
    failed_job: Stage6Job,
    *,
    args: argparse.Namespace,
    suffix: str = "refine",
) -> Stage6Job:
    """Construct a bounded refinement retry contract for a failed secondary."""
    target_path = (REPO_ROOT / failed_job.path).resolve()
    try:
        target_contents = target_path.read_text(encoding="utf-8")
    except OSError:
        target_contents = ""

    literal_old, literal_new, sync_reason = _synchronize_literal_pair(
        target_contents=target_contents,
        literal_old=failed_job.literal_old or args.literal_old,
        literal_new=failed_job.literal_new or args.literal_new,
    )
    if sync_reason is None and literal_old not in target_contents:
        import_sync = _sync_import_literal_pair(
            target_contents=target_contents,
            literal_old=args.literal_old,
            literal_new=args.literal_new,
        )
        if import_sync:
            literal_old, literal_new = import_sync
            sync_reason = "sync_import_line_refinement"

    message = args.message_template.format(
        path=failed_job.path,
        source=(failed_job.source or "rag4"),
        old=literal_old,
        new=literal_new,
    )
    return Stage6Job(
        path=failed_job.path,
        notes=failed_job.notes,
        lines=failed_job.lines,
        source=f"{failed_job.source or 'rag4'}:{suffix}",
        refinement_of=failed_job.path,
        literal_old=literal_old,
        literal_new=literal_new,
        sync_reason=sync_reason,
        message=message,
    )


def _candidate_rescue_paths(plan_payload: dict[str, Any], attempted: set[str]) -> list[str]:
    grouped = plan_payload.get("grouped_selection", {})
    dropped = grouped.get("dropped", [])
    rescue_paths: list[str] = []
    for entry in dropped:
        path = str(entry.get("path") or "")
        if not path or path in attempted:
            continue
        reason = str(entry.get("reason") or "")
        if reason == "max_entries_reached":
            rescue_paths.append(path)
            continue
        if reason == "unlinked_secondary":
            link_score = float(entry.get("link_score") or 0.0)
            if link_score >= 1.25:
                rescue_paths.append(path)
    return rescue_paths


def _build_rescue_job(path: str, *, failed_target: str, args: argparse.Namespace) -> Stage6Job:
    target_path = (REPO_ROOT / path).resolve()
    try:
        target_contents = target_path.read_text(encoding="utf-8")
    except OSError:
        target_contents = ""

    literal_old, literal_new, sync_reason = _synchronize_literal_pair(
        target_contents=target_contents,
        literal_old=args.literal_old,
        literal_new=args.literal_new,
    )
    if sync_reason is None and literal_old not in target_contents:
        import_sync = _sync_import_literal_pair(
            target_contents=target_contents,
            literal_old=args.literal_old,
            literal_new=args.literal_new,
        )
        if import_sync:
            literal_old, literal_new = import_sync
            sync_reason = "sync_import_line_rescue"

    message = args.message_template.format(
        path=path,
        source="rescue_swap",
        old=literal_old,
        new=literal_new,
    )
    return Stage6Job(
        path=path,
        source="rescue_swap",
        refinement_of=failed_target,
        literal_old=literal_old,
        literal_new=literal_new,
        sync_reason=sync_reason,
        message=message,
    )


def apply_failure_memory(
    *,
    jobs: list[Stage6Job],
    args: argparse.Namespace,
    manifest_version: int,
    lane_name: str,
    allowed_targets: list[str],
) -> tuple[list[Stage6Job], list[dict[str, Any]]]:
    adjusted: list[Stage6Job] = []
    findings: list[dict[str, Any]] = []
    for job in jobs:
        projected_message = args.message_template.format(
            path=job.path,
            source=(job.source or "rag4"),
            old=(job.literal_old or args.literal_old),
            new=(job.literal_new or args.literal_new),
        )
        decision = assess_target_risk(
            lane=lane_name,
            target=job.path,
            message=projected_message,
            manifest_version=manifest_version,
            retry_class=args.retry_class,
        )
        findings.append(
            {
                "target": job.path,
                "reason": decision.reason,
                "failures_by_class": decision.failures_by_class,
                "successes": decision.successes,
                "retry_class": args.retry_class,
                "rerouted": False,
            }
        )
        if decision.should_reroute_manual:
            continue
        adjusted.append(job)

    if not adjusted and args.fallback_target and args.retry_class in {"fallback_on_empty", "fallback_on_failure"}:
        fallback_path = args.fallback_target
        if not allowed_targets or any(fallback_path.startswith(prefix) for prefix in allowed_targets):
            adjusted.append(
                Stage6Job(path=fallback_path, source="fallback", refinement_of="failure_memory_reroute")
            )
            findings.append(
                {
                    "target": fallback_path,
                    "reason": "failure_memory fallback target",
                    "failures_by_class": {},
                    "successes": 0,
                    "retry_class": args.retry_class,
                    "rerouted": True,
                }
            )
    return adjusted, findings


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
    parser.add_argument(
        "--rag-max-targets",
        type=int,
        default=8,
        help="Maximum Stage RAG-4 targets before lane filtering/decomposition",
    )
    parser.add_argument("--max-entries", type=int, default=3, help="Maximum eligible Stage-6 entries to orchestrate per plan")
    parser.add_argument("--jobs-file", help="Optional manual JSON jobs definition")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH), help="Promotion manifest path")
    parser.add_argument(
        "--message-template",
        default="{path}:: replace exact text '{old}' with '{new}' (source={source})",
        help="Worker instruction message template",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without invoking Stage-5 manager")
    parser.add_argument("--plan-status", default="preview", help="Optional status used in trace entries")
    parser.add_argument("--fallback-target", help="Fallback target when RAG-4 returns no eligible jobs")
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument("--history-window", type=int, default=15, help="Git history window for Stage RAG-4")
    parser.add_argument("--min-confidence", type=int, default=1, help="Minimum RAG-4 confidence before enqueuing a target")
    parser.add_argument(
        "--retry-class",
        choices=["none", "fallback_on_empty", "fallback_on_failure", "adaptive_group_retry"],
        default="adaptive_group_retry",
        help="Retry policy class for Stage-6 fallback behavior",
    )
    parser.add_argument(
        "--group-failure-policy",
        choices=["abort", "continue_on_secondary_failure"],
        default="continue_on_secondary_failure",
        help="Behavior when a non-primary grouped target fails after bounded retries.",
    )
    parser.add_argument(
        "--max-secondary-retries",
        type=int,
        default=1,
        help="Maximum refinement retries for a failed secondary grouped target.",
    )
    parser.add_argument(
        "--max-secondary-rescues",
        type=int,
        default=1,
        help="Maximum rescue/swap attempts for failed secondary grouped targets.",
    )
    parser.add_argument("--literal-old", default=PLACEHOLDER_LITERAL, help="Literal old text for Stage-4 replacements")
    parser.add_argument("--literal-new", default=PLACEHOLDER_LITERAL_UPDATED, help="Literal new text for Stage-4 replacements")
    parser.add_argument("--min-lines", type=int, default=1, help="Minimum Stage-4 literal lines for the jobs")
    parser.add_argument(
        "--preferred-prefix",
        action="append",
        default=[],
        help="Preferred retrieval prefix for Stage RAG-4 ranking (repeatable).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest_cfg = load_manifest(manifest_path)
    lane_name = "stage6"
    versions = resolve_versions_for_lane(manifest_cfg.data, lane_name)
    lane_cfg = versions.get("lane", {})
    allowed_targets = lane_cfg.get("allowed_targets", ["bin/"])
    if not args.preferred_prefix:
        args.preferred_prefix = list(allowed_targets)

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
        jobs, grouped_selection = plan_to_jobs(plan, allowed_targets, args.max_entries, args.min_confidence)
        args.plan_details = plan
        if not jobs and args.fallback_target and args.retry_class in {"fallback_on_empty", "fallback_on_failure"}:
            fallback_path = args.fallback_target
            if allowed_targets and not any(fallback_path.startswith(prefix) for prefix in allowed_targets):
                raise SystemExit(f"[stage6] fallback target {fallback_path} is not allowed for the lane")
            jobs = [Stage6Job(path=fallback_path, source="fallback", refinement_of="empty_plan")]
            plan.setdefault("targets", []).append({"path": fallback_path, "source": "fallback"})
        plan_payload = {
            "plan_id": args.plan_id,
            "query": " ".join(args.query),
            "notes": args.notes,
            "targets": [job.path for job in jobs],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "grouped_selection": grouped_selection,
        }

    jobs, memory_findings = apply_failure_memory(
        jobs=jobs,
        args=args,
        manifest_version=manifest_cfg.version,
        lane_name=lane_name,
        allowed_targets=allowed_targets,
    )
    jobs = build_job_contracts(jobs, args)
    plan_payload["job_contracts"] = [
        {
            "path": job.path,
            "source": job.source,
            "refinement_of": job.refinement_of,
            "literal_old": job.literal_old,
            "literal_new": job.literal_new,
            "sync_reason": job.sync_reason,
            "message": job.message,
        }
        for job in jobs
    ]
    plan_payload["failure_memory_findings"] = memory_findings
    write_plan_history(
        args.plan_id,
        {
            "event_type": "planned",
            "state": "planned",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "plan_payload": plan_payload,
            "eligible_targets": [job.path for job in jobs],
            "query": " ".join(args.query),
            "retry_class": args.retry_class,
            "failure_memory_findings": memory_findings,
        },
    )
    if not jobs:
        print("[stage6] no eligible jobs found, nothing to run")
        write_plan_history(
            args.plan_id,
            {
                "event_type": "plan_empty",
                "state": "no_eligible_targets",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "statuses": [],
                "plan_payload": plan_payload,
            },
        )
        return 0

    env = build_promotion_env(lane_name, versions, manifest_cfg.version, manifest_path)
    statuses: list[dict[str, Any]] = []
    exit_code = 0
    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_started",
            "state": "running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statuses": [],
            "plan_payload": plan_payload,
        },
    )
    for idx, job in enumerate(jobs):
        status = run_stage5_job(job, args, env, idx)
        statuses.append(status)
        if status["return_code"] != 0:
            is_primary = idx == 0
            if is_primary:
                exit_code = int(status["return_code"])
                break

            retry_attempts = 0
            retry_success = False
            while (
                args.retry_class == "adaptive_group_retry"
                and retry_attempts < max(0, args.max_secondary_retries)
            ):
                retry_attempts += 1
                refinement_job = _build_refinement_job(
                    job,
                    args=args,
                    suffix=f"retry{retry_attempts}",
                )
                retry_status = run_stage5_job(refinement_job, args, env, len(statuses))
                retry_status["retry"] = True
                retry_status["retry_attempt"] = retry_attempts
                retry_status["retry_strategy"] = "secondary_refinement"
                statuses.append(retry_status)
                if retry_status["return_code"] == 0:
                    retry_success = True
                    break

            if retry_success:
                plan_payload.setdefault("refinements", []).append(
                    {
                        "target": job.path,
                        "result": "secondary_retry_succeeded",
                        "attempts": retry_attempts,
                    }
                )
                continue

            if args.group_failure_policy == "continue_on_secondary_failure":
                attempted_paths = {str(s.get("target")) for s in statuses if s.get("target")}
                rescue_candidates = _candidate_rescue_paths(plan_payload, attempted_paths)
                rescue_attempts = 0
                rescue_success = False
                for candidate in rescue_candidates:
                    if rescue_attempts >= max(0, args.max_secondary_rescues):
                        break
                    rescue_attempts += 1
                    rescue_job = _build_rescue_job(candidate, failed_target=job.path, args=args)
                    rescue_status = run_stage5_job(rescue_job, args, env, len(statuses))
                    rescue_status["retry"] = True
                    rescue_status["retry_attempt"] = rescue_attempts
                    rescue_status["retry_strategy"] = "secondary_swap"
                    rescue_status["rescued_from"] = job.path
                    statuses.append(rescue_status)
                    if rescue_status["return_code"] == 0:
                        rescue_success = True
                        plan_payload.setdefault("rescues", []).append(
                            {
                                "failed_target": job.path,
                                "rescue_target": candidate,
                                "result": "success",
                                "rescue_attempt": rescue_attempts,
                            }
                        )
                        break
                    plan_payload.setdefault("rescues", []).append(
                        {
                            "failed_target": job.path,
                            "rescue_target": candidate,
                            "result": "failed",
                            "rescue_attempt": rescue_attempts,
                        }
                    )

                if rescue_success:
                    continue

                plan_payload.setdefault("drops", []).append(
                    {
                        "target": job.path,
                        "reason": "secondary_failed_after_retry",
                        "retry_attempts": retry_attempts,
                        "rescue_attempts": rescue_attempts,
                    }
                )
                continue

            exit_code = int(status["return_code"])
            break

    if (
        exit_code != 0
        and args.retry_class in {"fallback_on_failure", "adaptive_group_retry"}
        and args.fallback_target
        and not any(job.source == "fallback" for job in jobs)
    ):
        print(f"[stage6] retrying plan {args.plan_id} with fallback target {args.fallback_target}")
        retry_job = Stage6Job(path=args.fallback_target, source="fallback", refinement_of="failed_primary_job")
        retry_status = run_stage5_job(retry_job, args, env, len(statuses))
        retry_status["retry"] = True
        statuses.append(retry_status)
        exit_code = int(retry_status["return_code"])
        plan_payload.setdefault("retries", []).append(
            {"target": retry_job.path, "status": "success" if retry_status["return_code"] == 0 else "failed"}
        )
        plan_payload["notes"] = plan_payload.get("notes") or "fallback retry"

    final_state = "succeeded" if exit_code == 0 else "failed"
    if exit_code == 0 and plan_payload.get("drops"):
        final_state = "partial_success"

    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_finished",
            "state": final_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statuses": statuses,
            "failure_code": exit_code,
            "plan_payload": plan_payload,
        },
    )

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
