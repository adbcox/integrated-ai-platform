#!/usr/bin/env python3
"""Manager-6 orchestrator for Stage-7 multi-plan execution."""

from __future__ import annotations

import argparse  # stage7-op  # stage7-op  # stage7-op  # stage7-op
import json
import os
import re
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
IMPORT_BASE_RE = re.compile(r"^(import|from)\s+")
SHELL_STRICT_RE = re.compile(r"^\s*set -euo pipefail\s*$")
SHELL_ASSIGNMENT_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*=")
SHELL_PRINT_RE = re.compile(r"^\s*(echo|printf)\b")
SHELL_RISKY_TOKEN_RE = re.compile(
    r"(\b(set|if|then|fi|elif|else|for|while|until|case|esac|do|done|exit|return|trap)\b|set\s*-[A-Za-z]+)",
    re.IGNORECASE,
)


def plan_history_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / f"{plan_id}.json"


def plan_checkpoint_path(plan_id: str) -> Path:
    return TRACE_DIR / "plans" / plan_id / "checkpoints.json"


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


def load_plan_history(plan_id: str) -> dict[str, Any]:
    history_path = plan_history_path(plan_id)
    if not history_path.exists():
        return {}
    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_checkpoints(plan_id: str) -> dict[str, Any]:
    path = plan_checkpoint_path(plan_id)
    if not path.exists():
        return {"plan_id": plan_id, "subplans": {}, "updated_at": None}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.setdefault("plan_id", plan_id)
            payload.setdefault("subplans", {})
            return payload
    except json.JSONDecodeError:
        pass
    return {"plan_id": plan_id, "subplans": {}, "updated_at": None}


def save_checkpoint(plan_id: str, status: dict[str, Any], *, attempt_index: int) -> None:
    checkpoint = load_checkpoints(plan_id)
    subplans = checkpoint.setdefault("subplans", {})
    subplan_id = str(status.get("subplan_id") or f"subplan-{len(subplans) + 1}")
    record = dict(status)
    record["attempt_index"] = int(attempt_index)
    record["checkpointed_at"] = datetime.now(timezone.utc).isoformat()
    subplans[subplan_id] = record
    checkpoint["updated_at"] = record["checkpointed_at"]
    path = plan_checkpoint_path(plan_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_resume_complete_status(status: str) -> bool:
    return status in {"success", "partial_success", "dropped_preflight"}


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


def _write_stage6_jobs_file(jobs: list[dict[str, Any]]) -> Path:
    payload = list(jobs)
    file_path = Path(tempfile.mkstemp(prefix="stage7-subplan-", suffix=".json")[1])
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def _single_line_import_base(value: str) -> str | None:
    if "\n" in value:
        return None
    text = value.strip()
    if not text:
        return None
    comment_idx = text.find("#")
    if comment_idx != -1:
        text = text[:comment_idx].rstrip()
    if IMPORT_BASE_RE.match(text):
        return text
    return None


def _target_supports_literal_contract(path: str, literal_old: str, literal_new: str) -> tuple[bool, str]:
    target_path = (REPO_ROOT / path).resolve()
    try:
        contents = target_path.read_text(encoding="utf-8")
    except OSError:
        return False, "unreadable_target"

    if literal_old in contents or literal_new in contents:
        return True, "literal_present"

    base_old = _single_line_import_base(literal_old)
    base_new = _single_line_import_base(literal_new)
    if base_old and base_new and base_old == base_new:
        for line in contents.splitlines():
            if line.strip().startswith(base_old):
                return True, "import_base_match"
    return False, "literal_mismatch_preflight"


def _derive_target_contract(path: str, literal_old: str, literal_new: str) -> dict[str, Any]:
    target_path = (REPO_ROOT / path).resolve()
    try:
        contents = target_path.read_text(encoding="utf-8")
    except OSError:
        return {
            "supported": False,
            "reason": "unreadable_target",
            "path": path,
        }

    supported, reason = _target_supports_literal_contract(path, literal_old, literal_new)
    if supported:
        return {
            "supported": True,
            "reason": reason,
            "path": path,
            "contract_strategy": "global_literal_contract",
            "literal_old": literal_old,
            "literal_new": literal_new,
        }

    is_shell_like = path.endswith(".sh")
    if not is_shell_like:
        first_line = contents.splitlines()[0].strip() if contents.splitlines() else ""
        if first_line.startswith("#!") and ("sh" in first_line or "bash" in first_line):
            is_shell_like = True
    if is_shell_like:
        def _safe_shell_literal_line(text: str) -> bool:
            stripped = text.strip()
            if not stripped:
                return False
            if stripped.startswith("#!"):
                return False
            if SHELL_RISKY_TOKEN_RE.search(stripped):
                return False
            return True

        for line in contents.splitlines():
            text = line.rstrip()
            if not text or text.lstrip().startswith("#"):
                continue
            if SHELL_STRICT_RE.match(text):
                continue
            if SHELL_ASSIGNMENT_RE.match(text) and _safe_shell_literal_line(text):
                return {
                    "supported": True,
                    "reason": "derived_shell_assignment_line",
                    "path": path,
                    "contract_strategy": "shell_assignment_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  # stage7-op",
                }
        for line in contents.splitlines():
            text = line.rstrip()
            if not text or text.lstrip().startswith("#"):
                continue
            if SHELL_PRINT_RE.match(text) and _safe_shell_literal_line(text):
                return {
                    "supported": True,
                    "reason": "derived_shell_print_line",
                    "path": path,
                    "contract_strategy": "shell_print_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  # stage7-op",
                }
        for line in contents.splitlines():
            text = line.rstrip()
            stripped = text.strip()
            if not stripped or stripped.startswith("#!"):
                continue
            if stripped.startswith("#") and _safe_shell_literal_line(text):
                return {
                    "supported": True,
                    "reason": "derived_shell_comment_line",
                    "path": path,
                    "contract_strategy": "shell_comment_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  [stage7-op]",
                }
        for line in contents.splitlines():
            if SHELL_STRICT_RE.match(line):
                base_old = line.rstrip()
                return {
                    "supported": True,
                    "reason": "derived_shell_strict_mode_line",
                    "path": path,
                    "contract_strategy": "shell_strict_mode_literal",
                    "literal_old": base_old,
                    "literal_new": f"{base_old}  # stage7-op",
                }
        return {
            "supported": False,
            "reason": "no_safe_anchor_script",
            "path": path,
            "contract_strategy": "shell_no_safe_anchor",
        }

    if path.endswith(".py"):
        for line in contents.splitlines():
            text = line.rstrip()
            if IMPORT_BASE_RE.match(text.strip()):
                return {
                    "supported": True,
                    "reason": "derived_python_import_line",
                    "path": path,
                    "contract_strategy": "python_import_literal",
                    "literal_old": text,
                    "literal_new": f"{text}  # stage7-op",
                }

    return {
        "supported": False,
        "reason": "literal_mismatch_preflight",
        "path": path,
    }


def run_stage6_subplan(
    *,
    subplan: dict[str, Any],
    args: argparse.Namespace,
    env: dict[str, str],
    op_index: int,
) -> dict[str, Any]:
    subplan_id = str(subplan.get("subplan_id") or f"subplan-{op_index + 1}")
    requested_targets = [str(t) for t in subplan.get("targets", []) if t]
    accepted_jobs: list[dict[str, Any]] = []
    accepted_targets: list[str] = []
    accepted_contracts: list[dict[str, Any]] = []
    dropped_targets: list[dict[str, str]] = []
    for target in requested_targets:
        contract = _derive_target_contract(target, args.literal_old, args.literal_new)
        if contract.get("supported"):
            accepted_targets.append(target)
            accepted_contracts.append(
                {
                    "path": target,
                    "contract_strategy": contract.get("contract_strategy", "global_literal_contract"),
                    "reason": contract.get("reason"),
                }
            )
            accepted_jobs.append(
                {
                    "path": target,
                    "source": "stage7-subplan",
                    "literal_old": contract.get("literal_old", args.literal_old),
                    "literal_new": contract.get("literal_new", args.literal_new),
                    "sync_reason": contract.get("reason"),
                }
            )
        else:
            dropped_targets.append({"path": target, "reason": str(contract.get("reason") or "literal_mismatch_preflight")})

    if not accepted_targets:
        rollback_contract = {
            "contract_version": "stage8-v1",
            "strategy": "preflight_drop_no_dispatch",
            "rollback_scope": [],
            "trigger_on_failure": False,
            "verification": "not_applicable_no_dispatch",
            "notes": "No stage6/stage5 dispatch occurred; no rollback action required.",
        }
        status = {
            "subplan_id": subplan_id,
            "targets": [],
            "target_contracts": [],
            "dropped_targets": dropped_targets,
            "status": "dropped_preflight",
            "return_code": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "strategy": "grouped_subplan",
            "rollback_contract": rollback_contract,
        }
        return status

    targets = accepted_targets
    jobs_file = _write_stage6_jobs_file(accepted_jobs)
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
        "--literal-old",
        args.literal_old,
        "--literal-new",
        args.literal_new,
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    proc = subprocess.run(cmd, env={**os.environ, **env})
    jobs_file.unlink(missing_ok=True)
    rollback_contract = {
        "contract_version": "stage8-v1",
        "strategy": "delegated_stage6_stage5_bounded_commit",
        "rollback_scope": targets,
        "trigger_on_failure": proc.returncode != 0,
        "verification": "stage6_return_code",
        "notes": "Rollback boundary remains delegated to stage6/stage5 guards; no global repo reset.",
    }
    status = {
        "subplan_id": subplan_id,
        "targets": targets,
        "target_contracts": accepted_contracts,
        "dropped_targets": dropped_targets,
        "status": "success" if proc.returncode == 0 else "failure",
        "return_code": proc.returncode,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "grouped_subplan",
        "rollback_contract": rollback_contract,
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


def _risk_rank(bucket: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(bucket, 2)


def _order_subplans(subplans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Risk/conflict-aware ordering for Stage-7 subplan execution.

    Lower-risk, non-overlapping families run first to reduce early brittle failures.
    """
    pending = [dict(item) for item in subplans]
    ordered: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    while pending:
        best_idx = 0
        best_key: tuple[int, int, float] | None = None
        for idx, subplan in enumerate(pending):
            meta = subplan.get("target_meta") or []
            families = {str(m.get("family") or "") for m in meta if m.get("family")}
            conflict_count = len(families & seen_families)
            worst_risk = max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in meta), default=2)
            confidence = float(subplan.get("confidence") or 0.0)
            key = (conflict_count, worst_risk, -confidence)
            if best_key is None or key < best_key:
                best_key = key
                best_idx = idx
        chosen = pending.pop(best_idx)
        meta = chosen.get("target_meta") or []
        families = sorted({str(m.get("family") or "") for m in meta if m.get("family")})
        chosen["execution_ordering"] = {
            "risk_rank": max((_risk_rank(str(m.get("risk_bucket") or "high")) for m in meta), default=2),
            "family_conflicts_with_prior": len(set(families) & seen_families),
            "families": families,
            "reason": "risk_conflict_aware_order",
        }
        seen_families.update(families)
        ordered.append(chosen)
    return ordered


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
    parser.add_argument("--literal-old", default="import argparse", help="Literal old text for delegated Stage-6 jobs")
    parser.add_argument(
        "--literal-new",
        default="import argparse  # stage7-op",
        help="Literal new text for delegated Stage-6 jobs",
    )

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
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an existing Stage-7 plan from persisted checkpoints and skip completed subplans.",
    )
    parser.add_argument(
        "--stop-after-subplans",
        type=int,
        default=0,
        help="Bounded test control: stop cleanly after N subplans and persist checkpoints.",
    )
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

    checkpoint = load_checkpoints(args.plan_id) if args.resume else {"subplans": {}}
    existing = load_plan_history(args.plan_id) if args.resume else {}
    if args.resume and existing.get("plan_payload"):
        plan_payload = dict(existing.get("plan_payload") or {})
        subplans = list(plan_payload.get("subplans", []))
        plan_payload.setdefault("resume_contract", {})
        plan_payload["resume_contract"].update(
            {
                "enabled": True,
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
                "resume_mode": "skip_completed_subplans",
            }
        )
    else:
        rag6_plan = run_stage_rag6(args)
        subplans = _order_subplans(list(rag6_plan.get("subplans", [])))

        plan_payload = {
            "plan_id": args.plan_id,
            "query": " ".join(args.query),
            "notes": args.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "subplans": subplans,
            "provenance": rag6_plan.get("provenance", {}),
            "reconciliation_contract": {
                "subplan_failure_policy": args.subplan_failure_policy,
                "rollback_model": "delegated_stage6_stage5_bounded_commit",
                "drop_model": "preflight_drop_when_literal_contract_unsupported",
                "checkpoint_model": "persisted_subplan_checkpoints_stage8_v1",
                "rollback_contract_version": "stage8-v1",
            },
            "resume_contract": {
                "enabled": True,
                "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
                "resume_mode": "skip_completed_subplans",
            },
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
    lane_cfg = versions.get("lane", {})
    statuses: list[dict[str, Any]] = []
    exit_code = 0
    resumed_completed: list[str] = []
    subplans_to_run: list[dict[str, Any]] = []
    checkpoint_subplans = checkpoint.get("subplans", {}) if isinstance(checkpoint, dict) else {}
    for subplan in subplans:
        subplan_id = str(subplan.get("subplan_id") or "")
        prior = checkpoint_subplans.get(subplan_id)
        if args.resume and isinstance(prior, dict) and _is_resume_complete_status(str(prior.get("status") or "")):
            resumed_completed.append(subplan_id)
            statuses.append(
                {
                    "subplan_id": subplan_id,
                    "status": "resumed_skip_completed",
                    "return_code": 0,
                    "resume_source_status": str(prior.get("status") or ""),
                    "strategy": "resume_skip",
                    "targets": prior.get("targets", []),
                    "rollback_contract": prior.get("rollback_contract"),
                }
            )
            continue
        subplans_to_run.append(subplan)

    write_plan_history(
        args.plan_id,
        {
            "event_type": "attempt_resumed" if args.resume else "attempt_started",
            "state": "running",
            "plan_payload": plan_payload,
            "statuses": statuses if args.resume else [],
            "resume_completed_subplans": resumed_completed,
        },
    )

    for idx, subplan in enumerate(subplans_to_run):
        status = run_stage6_subplan(subplan=subplan, args=args, env=env, op_index=idx)
        statuses.append(status)
        save_checkpoint(args.plan_id, status, attempt_index=idx + 1)

        if args.stop_after_subplans > 0 and (idx + 1) >= args.stop_after_subplans:
            plan_payload.setdefault("resume_events", []).append(
                {
                    "event": "paused_by_operator",
                    "processed_subplans": idx + 1,
                    "remaining_subplans": max(len(subplans_to_run) - (idx + 1), 0),
                    "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
                }
            )
            write_plan_history(
                args.plan_id,
                {
                    "event_type": "attempt_paused",
                    "state": "paused",
                    "statuses": statuses,
                    "plan_payload": plan_payload,
                    "failure_code": 0,
                },
            )
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
                return_code=0,
                promotion_outcome="paused",
                commit_hash=current_commit_hash(),
                extra={"plan_id": args.plan_id, "subplans": statuses, "plan_payload": plan_payload, "resume": args.resume},
            )
            append_trace(trace, trace_dir=TRACE_DIR)
            print(
                f"[stage7] paused after {idx + 1} subplan(s); checkpoints saved to {plan_checkpoint_path(args.plan_id)}"
            )
            return 0

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
            for split_idx, split_status in enumerate(split_statuses, start=1):
                save_checkpoint(args.plan_id, split_status, attempt_index=(idx + 1) * 100 + split_idx)
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
        extra={
            "plan_id": args.plan_id,
            "subplans": statuses,
            "plan_payload": plan_payload,
            "resume": args.resume,
            "resume_completed_subplans": resumed_completed,
            "checkpoint_path": str(plan_checkpoint_path(args.plan_id)),
        },
    )
    append_trace(trace, trace_dir=TRACE_DIR)

    if exit_code == 0:
        print(f"[stage7] orchestrated {len(statuses)} subplan execution(s) for plan {args.plan_id}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
