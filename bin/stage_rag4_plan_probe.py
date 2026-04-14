#!/usr/bin/env python3
"""Stage RAG-4 planning helper for Stage-6 multi-target orchestration."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
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


def _count_related_sources(related_entries: list[dict[str, Any]]) -> tuple[int, int]:
    sibling = 0
    git_history = 0
    for rel in related_entries:
        source = str(rel.get("source") or "")
        if source == "sibling":
            sibling += 1
        elif source == "git_history":
            git_history += 1
    return sibling, git_history


def _confidence_score(*, base_score: float, sibling_count: int, git_history_count: int, related_score: int) -> int:
    """Collapse retrieval quality signals into a bounded confidence bucket (1-10)."""
    # BM25 score contributes the strongest signal, while companion quality nudges tie-breaks.
    raw = (base_score * 3.0) + (sibling_count * 0.8) + (git_history_count * 1.2) + min(related_score / 220.0, 2.5)
    return max(1, min(10, int(math.floor(raw)) + 1))


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
    for entry in results:
        path = entry.get("path")
        if not path:
            continue
        related_entries = [rel for rel in entry.get("related", []) if rel.get("path")]
        related_files = [rel.get("path") for rel in related_entries]
        related_score = sum(len(rel.get("preview", "")) for rel in related_entries)
        sibling_count, git_history_count = _count_related_sources(related_entries)
        base_score = float(entry.get("score") or 0.0)
        confidence = _confidence_score(
            base_score=base_score,
            sibling_count=sibling_count,
            git_history_count=git_history_count,
            related_score=related_score,
        )
        rank_score = round(base_score + (git_history_count * 0.35) + (sibling_count * 0.15), 4)
        targets.append(
            {
                "path": path,
                "preview": entry.get("preview"),
                "related": related_files,
                "source": "stage_rag3",
                "base_score": base_score,
                "rank_score": rank_score,
                "confidence": confidence,
                "related_score": related_score,
                "selection_reason": {
                    "sibling_count": sibling_count,
                    "git_history_count": git_history_count,
                    "related_paths": related_files,
                },
            }
        )

    # Keep targets deterministic by retrieval score + companion strength.
    targets.sort(key=lambda item: (item["rank_score"], item["confidence"], item["path"]), reverse=True)
    targets = targets[: args.max_targets]

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
