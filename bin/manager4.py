#!/usr/bin/env python3
"""Manager-4 dispatcher bridging Stage-3/4/5 lanes with promotion awareness."""

from __future__ import annotations  # stage6-grouped

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
from promotion.failure_memory import assess_target_risk
from promotion.tracing import PromotionTraceEntry, append_trace, current_commit_hash
STAGE3_MANAGER = REPO_ROOT / "bin" / "stage3_manager.py"
STAGE4_MANAGER = REPO_ROOT / "bin" / "stage4_manager.py"
STAGE5_MANAGER = REPO_ROOT / "bin" / "stage5_manager.py"
LITERAL_RE = re.compile(r"replace exact text '(.+?)' with '(.+?)'", re.DOTALL)


class ManagerError(SystemExit):
    pass


def literal_line_count(message: str) -> tuple[int, int]:
    match = LITERAL_RE.search(message)
    if not match:
        return 0, 0
    return match.group(1).count("\n") + 1, match.group(2).count("\n") + 1


def ensure_message_anchor(message: str, target: str) -> str:
    target_name = Path(target).name
    if "::" in message and (target in message or target_name in message):
        return message
    if target in message or target_name in message:
        return f"{target}:: {message}"
    return f"{target}:: {message}"


def run(cmd: list[str], extra_env: dict[str, str] | None = None) -> int:
    env = os.environ.copy()
    if extra_env:
        env.update({k: v for k, v in extra_env.items() if v is not None})
    proc = subprocess.run(cmd, env=env)
    return proc.returncode


def dispatch_stage3(args: argparse.Namespace, extra_env: dict[str, str]) -> int:
    cmd = [
        sys.executable,
        str(STAGE3_MANAGER),
        "--query",
        args.query,
        "--target",
        args.target,
        "--message",
        args.message,
        "--commit-msg",
        args.commit_msg,
    ]
    if args.lines:
        cmd.extend(["--lines", args.lines])
    if args.notes:
        cmd.extend(["--notes", args.notes])
    return run(cmd, extra_env)


def dispatch_stage4(args: argparse.Namespace, extra_env: dict[str, str]) -> int:
    cmd = [
        sys.executable,
        str(STAGE4_MANAGER),
        "--query",
        args.query,
        "--target",
        args.target,
        "--message",
        args.message,
        "--commit-msg",
        args.commit_msg,
    ]
    if args.lines:
        cmd.extend(["--lines", args.lines])
    if args.notes:
        cmd.extend(["--notes", args.notes])
    if args.top:
        cmd.extend(["--top", str(args.top)])
    if args.window:
        cmd.extend(["--window", str(args.window)])
    return run(cmd, extra_env)


def dispatch_stage5(args: argparse.Namespace, batch_file: str, extra_env: dict[str, str]) -> int:
    cmd = [
        sys.executable,
        str(STAGE5_MANAGER),
        "--batch-file",
        batch_file,
        "--commit-msg",
        args.commit_msg,
    ]
    return run(cmd, extra_env)


def _stage5_entry_payload(
    *,
    query: str,
    target: str,
    message: str,
    lines: str,
    notes: str,
    top: int | None,
    window: int | None,
    max_total_lines: int | None,
) -> dict:
    payload: dict = {
        "query": query,
        "target": target,
        "message": ensure_message_anchor(message, target),
        "lines": lines,
    }
    if notes:
        payload["notes"] = notes
    if top is not None:
        payload["top"] = top
    if window is not None:
        payload["window"] = window
    if max_total_lines is not None:
        payload["max_total_lines"] = max_total_lines
    old_lines, new_lines = literal_line_count(message)
    literal_span = max(old_lines, new_lines)
    if 0 < literal_span < 3:
        # Stage-5 candidate batches may include one/two-line literal tweaks.
        # Keep Stage-4 bounds explicit so short literals do not fail by default.
        payload["min_lines"] = 1
    return payload


def _has_explicit_literal_blocks(message: str | None) -> bool:
    if not message:
        return False
    return bool(LITERAL_RE.search(message))


def create_stage5_batch(args: argparse.Namespace) -> Path:
    if not all([args.query, args.target, args.message]):
        raise ManagerError("Stage-5 auto batch requires --query/--target/--message")
    entries = [
        _stage5_entry_payload(
            query=args.query,
            target=args.target,
            message=args.message,
            lines=args.lines or "auto",
            notes=args.notes or "",
            top=args.top,
            window=args.window,
            max_total_lines=args.stage5_primary_max_total_lines,
        )
    ]

    secondary_args = [args.secondary_query, args.secondary_target, args.secondary_message]
    if any(secondary_args):
        if not all(secondary_args):
            raise ManagerError("Secondary Stage-5 entry requires query/target/message")
        entries.append(
            _stage5_entry_payload(
                query=args.secondary_query,
                target=args.secondary_target,
                message=args.secondary_message,
                lines=args.secondary_lines or "auto",
                notes=args.secondary_notes or "",
                top=args.secondary_top if args.secondary_top is not None else args.top,
                window=args.secondary_window if args.secondary_window is not None else args.window,
                max_total_lines=args.secondary_max_total_lines,
            )
        )

    timestamp = datetime.now(UTC).strftime("manager4-stage5-%Y%m%d-%H%M%S")
    batch_path = Path(tempfile.gettempdir()) / f"{timestamp}.json"
    batch_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return batch_path


def _classify_outcome(return_code: int | None, manual: bool) -> str:
    if manual:
        return "manual"
    if return_code == 0:
        return "success"
    return "failure"


def _trace_literal_lines(args: argparse.Namespace) -> int:
    old_lines, new_lines = literal_line_count(args.message or "")
    return max(old_lines, new_lines)


def record_trace(
    *,
    lane: str,
    lane_cfg: dict,
    lane_reason: str,
    versions: dict,
    manifest_path: Path,
    manifest_version: int,
    policy_status: str | None,
    args: argparse.Namespace,
    return_code: int | None,
    manual: bool,
    extra: dict[str, Any] | None = None,
) -> None:
    entry = PromotionTraceEntry(
        lane=lane,
        lane_label=lane_cfg.get("label", ""),
        lane_status=lane_cfg.get("status", ""),
        lane_reason=lane_reason,
        stage=versions.get("stage"),
        stage_version=versions.get("stage_version_name"),
        manager_version=versions.get("manager_version_name"),
        rag_version=versions.get("rag_version_name"),
        promotion_policy_status=policy_status,
        manifest_version=manifest_version,
        manifest_path=str(manifest_path),
        literal_lines=_trace_literal_lines(args),
        return_code=return_code,
        promotion_outcome=_classify_outcome(return_code, manual),
        commit_hash=current_commit_hash(),
        manual=manual,
        targets=[normalize_target(args.target)] if args.target else None,
        batch_file=args.batch_file,
        auto_stage=args.stage == "auto",
        auto_stage5_batch=args.batch_file is not None,
        extra=extra or {},
    )
    append_trace(entry)


def infer_lane(args: argparse.Namespace, desired_stage: str) -> str:
    if args.lane != "auto":
        return args.lane
    if desired_stage == "stage5" or args.batch_file or args.secondary_target:
        return "candidate"
    return "production"


def normalize_target(target: str | None) -> str:
    if not target:
        return ""
    return target.lstrip("./")


def is_target_allowed(target: str, allowed_prefixes: list[str]) -> bool:
    if not target or not allowed_prefixes:
        return True
    return any(target.startswith(prefix) for prefix in allowed_prefixes)


def build_promotion_env(
    lane_name: str,
    versions: dict,
    manifest_version: int,
    manifest_path: Path,
    lane_reason: str,
) -> dict[str, str]:
    lane = versions.get("lane", {})
    stage_version_name = versions.get("stage_version_name")
    manager_version_name = versions.get("manager_version_name")
    rag_version_name = versions.get("rag_version_name")
    stage_name = versions.get("stage")
    env = {
        "PROMOTION_LANE": lane_name,
        "PROMOTION_LANE_STATUS": lane.get("status", ""),
        "PROMOTION_LANE_LABEL": lane.get("label", ""),
        "PROMOTION_LANE_REASON": lane_reason,
        "PROMOTION_STAGE_VERSION": stage_version_name or "",
        "PROMOTION_STAGE_NAME": stage_name or "",
        "PROMOTION_MANAGER_VERSION": manager_version_name or "",
        "PROMOTION_RAG_VERSION": rag_version_name or "",
        "PROMOTION_MANIFEST_VERSION": str(manifest_version),
        "PROMOTION_MANIFEST_PATH": str(manifest_path),
    }
    allowed = lane.get("allowed_targets")
    if allowed:
        env["PROMOTION_ALLOWED_TARGETS"] = ",".join(allowed)
    return env


def handle_manual_lane(lane_cfg: dict, reason: str, manifest_path: Path) -> None:
    label = lane_cfg.get("label", "manual lane")
    notes = lane_cfg.get("notes", "")
    print(f"[manager4] routing to manual lane '{label}': {reason}")
    if notes:
        print(f"[manager4] manual lane notes: {notes}")
    print(
        "[manager4] use Codex/manual workflow or rerun with an explicit lane once"
        f" the manifest ({manifest_path}) is updated."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Manager-4 dispatcher")
    parser.add_argument("--query", help="Stage RAG query (Stage-3/Stage-4)")
    parser.add_argument("--target", help="Target file (Stage-3/Stage-4)")
    parser.add_argument("--message", help="Worker instruction message")
    parser.add_argument("--commit-msg", required=True, help="Commit message")
    parser.add_argument("--lines", default="auto")
    parser.add_argument("--notes", default="")
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--stage", choices=["auto", "stage3", "stage4", "stage5"], default="auto")
    parser.add_argument("--stage4-threshold", type=int, default=3, help="Literal line-count threshold for auto Stage-4 routing")
    parser.add_argument("--batch-file", help="JSON batch file for Stage-5")
    parser.add_argument("--stage5-primary-max-total-lines", type=int, help="Per-entry budget override for auto Stage-5 primary entry")
    parser.add_argument("--secondary-query")
    parser.add_argument("--secondary-target")
    parser.add_argument("--secondary-message")
    parser.add_argument("--secondary-lines", default="auto")
    parser.add_argument("--secondary-notes", default="")
    parser.add_argument("--secondary-top", type=int)
    parser.add_argument("--secondary-window", type=int)
    parser.add_argument("--secondary-max-total-lines", type=int)
    parser.add_argument("--lane", choices=["auto", "production", "candidate", "manual"], default="auto", help="Explicit lane override")
    parser.add_argument(
        "--promotion-manifest",
        default=str(MANIFEST_PATH),
        help="Path to the promotion manifest JSON (defaults to config/promotion_manifest.json)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.promotion_manifest).resolve()
    manifest_cfg = load_manifest(manifest_path)
    manifest_data = manifest_cfg.data

    old_lines, new_lines = literal_line_count(args.message or "")
    literal_span = max(old_lines, new_lines)

    desired_stage = args.stage
    if desired_stage == "auto":
        if args.batch_file:
            desired_stage = "stage5"
        elif literal_span >= args.stage4_threshold:
            desired_stage = "stage4"
        else:
            desired_stage = "stage3"

    if desired_stage in {"stage3", "stage4"} and (not args.query or not args.target or not args.message):
        raise ManagerError(f"{desired_stage} routing requires --query/--target/--message")
    if desired_stage == "stage5" and not (args.batch_file or args.secondary_target or args.secondary_query or args.secondary_message or (args.query and args.target and args.message)):
        raise ManagerError("Stage-5 routing requires either --batch-file or primary literal parameters")

    lane = infer_lane(args, desired_stage)
    lane_reason = f"forced:{args.lane}" if args.lane != "auto" else f"auto:{lane}"
    versions = resolve_versions_for_lane(manifest_data, lane)
    lane_cfg = versions.get("lane", {})
    allowed_targets = lane_cfg.get("allowed_targets") or []

    targets_to_check: list[str] = []
    if args.target:
        targets_to_check.append(normalize_target(args.target))
    if args.secondary_target:
        targets_to_check.append(normalize_target(args.secondary_target))

    disallowed_target: str | None = None
    if allowed_targets:
        for candidate_target in targets_to_check:
            if not is_target_allowed(candidate_target, allowed_targets):
                disallowed_target = candidate_target
                break
    if disallowed_target:
        lane = "manual"
        lane_reason = f"manual:target:{disallowed_target}"
        versions = resolve_versions_for_lane(manifest_data, lane)
        lane_cfg = versions.get("lane", {})
        allowed_targets = lane_cfg.get("allowed_targets") or []

    manifest_version = manifest_cfg.version
    promotion_policy = manifest_data.get("promotion_policy", {})
    policy_status = promotion_policy.get("last_decision", {}).get("status")

    memory_findings: list[dict[str, Any]] = []
    if lane in {"candidate", "stage6"}:
        candidate_inputs: list[tuple[str, str]] = []
        if args.target and args.message:
            candidate_inputs.append((normalize_target(args.target), args.message))
        if args.secondary_target and args.secondary_message:
            candidate_inputs.append((normalize_target(args.secondary_target), args.secondary_message))
        for target, message in candidate_inputs:
            decision = assess_target_risk(
                lane=lane,
                target=target,
                message=message,
                manifest_version=manifest_version,
                retry_class="none",
            )
            memory_findings.append(
                {
                    "target": target,
                    "failures_by_class": decision.failures_by_class,
                    "successes": decision.successes,
                    "should_force_anchor": decision.should_force_anchor,
                    "should_reroute_manual": decision.should_reroute_manual,
                    "reason": decision.reason,
                }
            )
            if decision.should_reroute_manual:
                lane = "manual"
                lane_reason = f"manual:memory:{target}:literal_shell_risky"
                versions = resolve_versions_for_lane(manifest_data, lane)
                lane_cfg = versions.get("lane", {})
                allowed_targets = lane_cfg.get("allowed_targets") or []
                break
            if decision.should_force_anchor:
                if args.target and normalize_target(args.target) == target and args.message:
                    args.message = ensure_message_anchor(args.message, target)
                if args.secondary_target and normalize_target(args.secondary_target) == target and args.secondary_message:
                    args.secondary_message = ensure_message_anchor(args.secondary_message, target)

    batch_file_arg = args.batch_file
    auto_batch_used = False

    if lane == "manual":
        handle_manual_lane(lane_cfg, lane_reason, manifest_path)
        record_trace(
            lane=lane,
            lane_cfg=lane_cfg,
            lane_reason=lane_reason,
            versions=versions,
            manifest_path=manifest_path,
            manifest_version=manifest_version,
            policy_status=policy_status,
            args=args,
            return_code=2,
            manual=True,
            extra={
                "manual_reason": lane_reason,
                "job_stage_argument": args.stage,
                "allowed_check_targets": targets_to_check,
                "lane_allowed_targets": allowed_targets,
                "secondary_target": args.secondary_target,
                "notes": args.notes or None,
                "lane_regression_pack": lane_cfg.get("regression_pack"),
                "failure_memory_findings": memory_findings,
            },
        )
        return 2

    lane_stage_name = versions.get("stage")
    routed_stage = desired_stage
    if lane == "candidate" and lane_stage_name:
        routed_stage = lane_stage_name
    if routed_stage not in {"stage3", "stage4", "stage5"}:
        raise ManagerError(f"Unsupported stage '{routed_stage}' for lane '{lane}'")

    # Stage-5 routes through stage4_manager for each entry. Guard prompt shape before
    # dispatch so malformed non-literal instructions do not count as avoidable run failures.
    if lane == "candidate" and routed_stage == "stage5" and not args.batch_file:
        stage5_messages: list[tuple[str, str | None]] = []
        if args.target:
            stage5_messages.append((normalize_target(args.target), args.message))
        if args.secondary_target:
            stage5_messages.append((normalize_target(args.secondary_target), args.secondary_message))
        malformed_target = next(
            (target for target, message in stage5_messages if not _has_explicit_literal_blocks(message)),
            None,
        )
        if malformed_target:
            lane = "manual"
            lane_reason = f"manual:prompt_shape:{malformed_target}:stage5_literal_required"
            versions = resolve_versions_for_lane(manifest_data, lane)
            lane_cfg = versions.get("lane", {})
            allowed_targets = lane_cfg.get("allowed_targets") or []
    if lane == "manual":
        handle_manual_lane(lane_cfg, lane_reason, manifest_path)
        record_trace(
            lane=lane,
            lane_cfg=lane_cfg,
            lane_reason=lane_reason,
            versions=versions,
            manifest_path=manifest_path,
            manifest_version=manifest_version,
            policy_status=policy_status,
            args=args,
            return_code=2,
            manual=True,
            extra={
                "manual_reason": lane_reason,
                "job_stage_argument": args.stage,
                "allowed_check_targets": targets_to_check,
                "lane_allowed_targets": allowed_targets,
                "secondary_target": args.secondary_target,
                "notes": args.notes or None,
                "lane_regression_pack": lane_cfg.get("regression_pack"),
                "failure_memory_findings": memory_findings,
            },
        )
        return 2

    promotion_env = build_promotion_env(lane, versions, manifest_version, manifest_path, lane_reason)

    auto_batch_path: Path | None = None
    if routed_stage == "stage5" and not batch_file_arg:
        auto_batch_path = create_stage5_batch(args)
        batch_file_arg = str(auto_batch_path)
        auto_batch_used = True

    if routed_stage == "stage3":
        retcode = dispatch_stage3(args, promotion_env)
    elif routed_stage == "stage4":
        retcode = dispatch_stage4(args, promotion_env)
    else:
        retcode = dispatch_stage5(args, batch_file_arg, promotion_env)
    if auto_batch_path and auto_batch_path.exists():
        auto_batch_path.unlink(missing_ok=True)

    record_trace(
        lane=lane,
        lane_cfg=lane_cfg,
        lane_reason=lane_reason,
        versions=versions,
        manifest_path=manifest_path,
        manifest_version=manifest_version,
        policy_status=policy_status,
        args=args,
        return_code=retcode,
        manual=False,
        extra={
            "dispatched_stage": routed_stage,
            "job_stage_argument": args.stage,
            "allowed_check_targets": targets_to_check,
            "lane_allowed_targets": allowed_targets,
            "secondary_target": args.secondary_target,
            "batch_file": batch_file_arg,
            "auto_stage5_batch": auto_batch_used,
            "notes": args.notes or None,
            "lane_regression_pack": lane_cfg.get("regression_pack"),
            "commit_msg": args.commit_msg,
            "failure_memory_findings": memory_findings,
        },
    )
    if retcode != 0:
        return retcode
    version_label = versions.get("stage_version_name") or routed_stage
    print(f"[manager4] dispatched to {routed_stage} (lane={lane}, stage_version={version_label})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
