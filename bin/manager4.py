#!/usr/bin/env python3
"""Manager-4 dispatcher bridging Stage-3/4/5 lanes."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
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


def run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd)
    return proc.returncode


def dispatch_stage3(args: argparse.Namespace) -> int:
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
    return run(cmd)


def dispatch_stage4(args: argparse.Namespace) -> int:
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
    return run(cmd)


def dispatch_stage5(args: argparse.Namespace, batch_file: str) -> int:
    cmd = [
        sys.executable,
        str(STAGE5_MANAGER),
        "--batch-file",
        batch_file,
        "--commit-msg",
        args.commit_msg,
    ]
    return run(cmd)


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
    args = parser.parse_args()

    old_lines, new_lines = literal_line_count(args.message or "")
    literal_span = max(old_lines, new_lines)

    routed_stage = args.stage
    if routed_stage == "auto":
        if args.batch_file:
            routed_stage = "stage5"
        elif literal_span >= args.stage4_threshold:
            routed_stage = "stage4"
        else:
            routed_stage = "stage3"

    if routed_stage in {"stage3", "stage4"} and (not args.query or not args.target or not args.message):
        raise ManagerError(f"{routed_stage} routing requires --query/--target/--message")
    if routed_stage == "stage5" and not (args.batch_file or args.secondary_target or args.secondary_query or args.secondary_message or (args.query and args.target and args.message)):
        raise ManagerError("Stage-5 routing requires either --batch-file or primary literal parameters")

    auto_batch_path: Path | None = None
    batch_file_arg = args.batch_file
    if routed_stage == "stage5" and not batch_file_arg:
        auto_batch_path = create_stage5_batch(args)
        batch_file_arg = str(auto_batch_path)

    auto_batch_used = auto_batch_path is not None

    if routed_stage == "stage3":
        retcode = dispatch_stage3(args)
    elif routed_stage == "stage4":
        retcode = dispatch_stage4(args)
    else:
        retcode = dispatch_stage5(args, batch_file_arg)
    if auto_batch_path and auto_batch_path.exists():
        auto_batch_path.unlink(missing_ok=True)

    append_trace(
        {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "stage": routed_stage,
            "auto_stage": args.stage == "auto",
            "literal_lines": literal_span,
            "return_code": retcode,
            "target": args.target,
            "batch_file": batch_file_arg,
            "auto_stage5_batch": auto_batch_used,
            "secondary_target": args.secondary_target,
        }
    )
    if retcode != 0:
        return retcode
    print(f"[manager4] dispatched to {routed_stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
