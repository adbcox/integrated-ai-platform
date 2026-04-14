#!/usr/bin/env python3
"""Manager-4 dispatcher bridging Stage-3/4/5 lanes."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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


def dispatch_stage5(args: argparse.Namespace) -> int:
    if not args.batch_file:
        raise ManagerError("Stage-5 routing requires --batch-file")
    cmd = [
        sys.executable,
        str(STAGE5_MANAGER),
        "--batch-file",
        args.batch_file,
        "--commit-msg",
        args.commit_msg,
    ]
    return run(cmd)


def append_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        json.dump(entry, fh, ensure_ascii=False)
        fh.write("\n")


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
    if routed_stage == "stage5" and not args.batch_file:
        raise ManagerError("Stage-5 routing requires --batch-file")

    if routed_stage == "stage3":
        retcode = dispatch_stage3(args)
    elif routed_stage == "stage4":
        retcode = dispatch_stage4(args)
    else:
        retcode = dispatch_stage5(args)

    append_trace(
        {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "stage": routed_stage,
            "auto_stage": args.stage == "auto",
            "literal_lines": literal_span,
            "return_code": retcode,
            "target": args.target,
            "batch_file": args.batch_file,
        }
    )
    if retcode != 0:
        return retcode
    print(f"[manager4] dispatched to {routed_stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
