#!/usr/bin/env python3
"""Manager-4 dispatcher bridging Stage-3/4/5 lanes with promotion awareness."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
STAGE3_MANAGER = REPO_ROOT / "bin" / "stage3_manager.py"
STAGE4_MANAGER = REPO_ROOT / "bin" / "stage4_manager.py"
STAGE5_MANAGER = REPO_ROOT / "bin" / "stage5_manager.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "manager4"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
LITERAL_RE = re.compile(r"replace exact text '(.+?)' with '(.+?)'", re.DOTALL)


class ManagerError(SystemExit):
    pass


def literal_line_count(message: str) -> tuple[int, int]:
    match = LITERAL_RE.search(message)
    if not match:
        return 0, 0
    return match.group(1).count("\n") + 1, match.group(2).count("\n") + 1


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


def append_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        json.dump(entry, fh, ensure_ascii=False)
        fh.write("\n")


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
        "message": message,
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
    return payload


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
    parser.add_argument("--stage4-threshold", type=int, default=3, help="Line count threshold for Stage-4 routing")
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

    batch_file_arg = args.batch_file
    auto_batch_used = False

    if lane == "manual":
        handle_manual_lane(lane_cfg, lane_reason, manifest_path)
        trace_time = datetime.now(UTC).isoformat(timespec="seconds")
        append_trace(
            {
                "timestamp": trace_time,
                "lane": lane,
                "lane_status": lane_cfg.get("status"),
                "lane_label": lane_cfg.get("label"),
                "lane_reason": lane_reason,
                "manual_reason": lane_reason,
                "stage": desired_stage,
                "job_stage_argument": args.stage,
                "stage_version": versions.get("stage_version_name"),
                "manager_version": versions.get("manager_version_name"),
                "rag_version": versions.get("rag_version_name"),
                "manifest_version": manifest_version,
                "manifest_path": str(manifest_path),
                "promotion_policy_status": policy_status,
                "literal_lines": literal_span,
                "return_code": 2,
                "manual": True,
                "target": args.target,
                "secondary_target": args.secondary_target,
                "lane_allowed_targets": allowed_targets,
                "allowed_check_targets": targets_to_check,
                "batch_file": batch_file_arg,
                "auto_stage": args.stage == "auto",
                "auto_stage5_batch": False,
                "notes": args.notes or None,
                "lane_regression_pack": lane_cfg.get("regression_pack"),
            }
        )
        return 2

    lane_stage_name = versions.get("stage")
    routed_stage = desired_stage
    if lane == "candidate" and lane_stage_name:
        routed_stage = lane_stage_name
    if routed_stage not in {"stage3", "stage4", "stage5"}:
        raise ManagerError(f"Unsupported stage '{routed_stage}' for lane '{lane}'")

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

    trace_time = datetime.now(UTC).isoformat(timespec="seconds")
    append_trace(
        {
            "timestamp": trace_time,
            "lane": lane,
            "lane_status": lane_cfg.get("status"),
            "lane_label": lane_cfg.get("label"),
            "lane_reason": lane_reason,
            "stage": routed_stage,
            "dispatched_stage": routed_stage,
            "job_stage_argument": args.stage,
            "stage_version": versions.get("stage_version_name"),
            "manager_version": versions.get("manager_version_name"),
            "rag_version": versions.get("rag_version_name"),
            "manifest_version": manifest_version,
            "manifest_path": str(manifest_path),
            "promotion_policy_status": policy_status,
            "auto_stage": args.stage == "auto",
            "literal_lines": literal_span,
            "return_code": retcode,
            "target": args.target,
            "secondary_target": args.secondary_target,
            "lane_allowed_targets": allowed_targets,
            "allowed_check_targets": targets_to_check,
            "batch_file": batch_file_arg,
            "auto_stage5_batch": auto_batch_used,
            "notes": args.notes or None,
            "lane_regression_pack": lane_cfg.get("regression_pack"),
            "commit_msg": args.commit_msg,
        }
    )
    if retcode != 0:
        return retcode
    print(f"[manager4] dispatched to {routed_stage} (lane={lane})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
