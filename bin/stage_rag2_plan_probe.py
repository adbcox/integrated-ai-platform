#!/usr/bin/env python3
"""Stage RAG-2 planning logger for Stage-4 multi-line probes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEARCH_BIN = REPO_ROOT / "bin" / "stage_rag2_search.py"
LOG_DIR = REPO_ROOT / "artifacts" / "stage_rag2"
LOG_FILE = LOG_DIR / "usage.jsonl"


def run_search(args: argparse.Namespace) -> str:
    if not SEARCH_BIN.exists():
        raise SystemExit(f"missing Stage RAG-2 retriever: {SEARCH_BIN}")
    cmd = [
        sys.executable,
        str(SEARCH_BIN),
        "--top",
        str(args.top),
        "--window",
        str(args.window),
        "--preview-lines",
        str(args.preview_lines),
    ]
    if args.json:
        cmd.append("--json")
    cmd += args.query
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    output = proc.stdout
    print(output, end="")
    return output


def prompt(default: str = "") -> str:
    try:
        return input().strip() or default
    except EOFError:
        return default


def append_log(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def clamp_preview(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-2 planning helper")
    parser.add_argument("query", nargs="+", help="natural-language description of the probe goal")
    parser.add_argument("--plan-id", help="identifier for this probe/run")
    parser.add_argument("--stage", default="stage4", help="stage tag (default: stage4)")
    parser.add_argument("--top", type=int, default=6, help="number of ranked anchors to display")
    parser.add_argument("--window", type=int, default=20, help="context window (lines) for Stage RAG-2 expansions")
    parser.add_argument("--preview-lines", type=int, default=18, help="lines to show per snippet")
    parser.add_argument("--selected-path", help="skip prompt/log this file path")
    parser.add_argument("--selected-lines", help="skip prompt/log this line range")
    parser.add_argument("--notes", help="extra context for downstream logging")
    parser.add_argument("--json", action="store_true", help="emit machine readable list for automation")
    parser.add_argument("--skip-log", action="store_true", help="run retrieval without recording a log entry")
    args = parser.parse_args()

    search_output = run_search(args)

    selected_path = args.selected_path
    selected_lines = args.selected_lines
    if not selected_path and not args.skip_log:
        print("Selected file path (relative, blank to skip logging):", end=" ")
        selected_path = prompt()
    if selected_path and not selected_lines and not args.skip_log:
        print("Anchor line range (e.g. 90-118):", end=" ")
        selected_lines = prompt()

    notes = args.notes or ""
    if not notes and not args.skip_log:
        print("Optional notes/context (blank to skip):", end=" ")
        notes = prompt()

    if args.skip_log or not selected_path:
        return 0

    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stage": args.stage,
        "plan_id": args.plan_id,
        "query": " ".join(args.query),
        "selected_path": selected_path,
        "selected_lines": selected_lines,
        "notes": notes or None,
        "preview": clamp_preview(search_output),
    }
    append_log(entry)
    print(f"[stage-rag2] logged selection for {selected_path} ({args.stage}) -> {LOG_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
