#!/usr/bin/env python3
"""Stage RAG-4 planning helper for Stage-6 multi-target orchestration."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_RAG3_SEARCH = REPO_ROOT / "bin" / "stage_rag3_search.py"
LOG_DIR = REPO_ROOT / "artifacts" / "stage_rag4"
LOG_FILE = LOG_DIR / "usage.jsonl"


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(STAGE_RAG3_SEARCH),
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
    cmd += args.query
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def append_log(entry: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-4 planning helper")
    parser.add_argument("query", nargs="+", help="Natural language probe for Stage-6")
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--max-targets", type=int, default=4)
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument(
        "--history-window",
        type=int,
        default=15,
        help="Git log window for partner discovery",
    )
    parser.add_argument("--notes", help="Optional notes/context for the plan")
    args = parser.parse_args()

    search_payload = run_search(args)
    results = search_payload.get("results", [])

    targets: list[dict[str, Any]] = []
    for entry in results[: args.max_targets]:
        targets.append(
            {
                "path": entry.get("path"),
                "preview": entry.get("preview"),
                "related": [rel.get("path") for rel in entry.get("related", []) if rel.get("path")],
                "source": "stage_rag3",
            }
        )

    plan = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "plan_id": args.plan_id,
        "stage": "stage6",
        "query": " ".join(args.query),
        "targets": targets,
        "notes": args.notes,
        "preview_window": args.preview_lines,
        "provenance": {
            "query_tokens": args.query,
            "result_count": len(results),
            "related_limit": args.related_limit,
            "history_window": args.history_window,
        },
        "raw_payload": search_payload,
    }

    append_log(plan)
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
