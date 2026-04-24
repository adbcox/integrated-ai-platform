#!/usr/bin/env python3
"""Stage RAG-3 planning helper for Stage-5 multi-file batches."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEARCH_BIN = REPO_ROOT / "bin" / "stage_rag3_search.py"
LOG_DIR = REPO_ROOT / "artifacts" / "stage_rag3"
LOG_FILE = LOG_DIR / "usage.jsonl"


def run_search(args: argparse.Namespace) -> dict:
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
    cmd += args.query
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    print(proc.stdout, end="")
    return data


def append_log(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def prompt(text: str) -> str:
    try:
        return input(text).strip()
    except EOFError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-3 planning logger")
    parser.add_argument("query", nargs="+", help="Natural language probe description")
    parser.add_argument("--stage", default="stage5")
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--selected-path", help="Primary file path (optional prompt skipped if provided)")
    parser.add_argument("--selected-lines", help="Primary line range")
    parser.add_argument("--secondary-path", help="Secondary file path for multi-target runs")
    parser.add_argument("--secondary-lines", help="Secondary line range")
    parser.add_argument("--notes", help="Optional notes")
    args = parser.parse_args()

    search_payload = run_search(args)

    primary_path = args.selected_path or prompt("Primary file path (blank to skip logging): ")
    primary_lines = args.selected_lines or ""
    if primary_path and not primary_lines:
        primary_lines = prompt("Primary line range (e.g. 40-55): ")
    secondary_path = args.secondary_path or prompt("Secondary file path (optional): ")
    secondary_lines = args.secondary_lines or ""
    if secondary_path and not secondary_lines:
        secondary_lines = prompt("Secondary line range: ")
    notes = args.notes or prompt("Notes/context (blank to skip): ")

    if not primary_path:
        return 0

    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stage": args.stage,
        "plan_id": args.plan_id,
        "query": " ".join(args.query),
        "primary_path": primary_path,
        "primary_lines": primary_lines or None,
        "secondary_path": secondary_path or None,
        "secondary_lines": secondary_lines or None,
        "notes": notes or None,
        "preview": search_payload,
    }
    append_log(entry)
    print(f"[stage-rag3] logged plan {args.plan_id} -> {LOG_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
