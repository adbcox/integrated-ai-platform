#!/usr/bin/env python3
"""Manager-3 (beta) dispatcher bridging Stage-3 and Stage-4 managers."""

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
TRACE_DIR = REPO_ROOT / "artifacts" / "manager3"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
LITERAL_RE = re.compile(r"replace exact text '(.+?)' with '(.+?)'", re.DOTALL)


class ManagerError(SystemExit):
    pass


def parse_literal_line_count(message: str) -> tuple[int, int]:
    match = LITERAL_RE.search(message)
    if not match:
        return 0, 0
    old_literal, new_literal = match.group(1), match.group(2)
    return line_count(old_literal), line_count(new_literal)


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def dispatch(stage: str, args: argparse.Namespace, literal_lines: int) -> tuple[int, str | None]:
    cmd = [sys.executable]
    if stage == "stage3":
        if not STAGE3_MANAGER.exists():
            raise ManagerError("Stage-3 manager missing")
        cmd.append(str(STAGE3_MANAGER))
        cmd.extend(
            [
                "--query",
                args.query,
                "--target",
                args.target,
                "--message",
                args.message,
                "--commit-msg",
                args.commit_msg,
            ]
        )
        if args.lines:
            cmd.extend(["--lines", args.lines])
        if args.notes:
            cmd.extend(["--notes", args.notes])
    elif stage == "stage4":
        if not STAGE4_MANAGER.exists():
            raise ManagerError("Stage-4 manager missing")
        cmd.append(str(STAGE4_MANAGER))
        cmd.extend(
            [
                "--query",
                args.query,
                "--target",
                args.target,
                "--message",
                args.message,
                "--commit-msg",
                args.commit_msg,
            ]
        )
        if args.lines:
            cmd.extend(["--lines", args.lines])
        if args.notes:
            cmd.extend(["--notes", args.notes])
        if args.top:
            cmd.extend(["--top", str(args.top)])
        if args.window:
            cmd.extend(["--window", str(args.window)])
    else:
        raise ManagerError(f"unsupported stage '{stage}'")

    proc = subprocess.run(cmd)
    return proc.returncode, "stage3" if stage == "stage3" else "stage4"


def append_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        json.dump(entry, fh, ensure_ascii=False)
        fh.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manager-3 dispatcher")
    parser.add_argument("--query", required=True, help="Stage RAG query")
    parser.add_argument("--target", required=True, help="Target file")
    parser.add_argument("--message", required=True, help="Worker instruction message")
    parser.add_argument("--commit-msg", required=True, help="Commit message")
    parser.add_argument("--lines", default="auto", help="Anchor lines when logging")
    parser.add_argument("--notes", default="", help="Optional planning notes")
    parser.add_argument("--top", type=int, default=6, help="Stage RAG top results for Stage-4 routing")
    parser.add_argument("--window", type=int, default=20, help="Stage RAG window for Stage-4 routing")
    parser.add_argument("--stage", choices=["auto", "stage3", "stage4"], default="auto")
    parser.add_argument("--min-multiline", type=int, default=3, help="Line threshold for Stage-4 auto routing")
    args = parser.parse_args()

    old_lines, new_lines = parse_literal_line_count(args.message)
    largest_literal = max(old_lines, new_lines)

    stage = args.stage
    if stage == "auto":
        stage = "stage4" if largest_literal >= args.min_multiline else "stage3"

    retcode, routed_stage = dispatch(stage, args, largest_literal)

    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "query": args.query,
        "target": args.target,
        "stage": routed_stage,
        "auto_stage": args.stage == "auto",
        "literal_lines": largest_literal,
        "return_code": retcode,
    }
    append_trace(entry)

    if retcode != 0:
        return retcode
    print(f"[manager3] dispatched to {routed_stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
