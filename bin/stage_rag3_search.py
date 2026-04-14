#!/usr/bin/env python3
"""Stage RAG-3 hybrid retriever.

Extends Stage RAG-2 by pairing lexical/structural hits with nearby related files
so multi-file edits (Stage-5) can pre-select anchors for both primary and
secondary targets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_RAG2_SEARCH = REPO_ROOT / "bin" / "stage_rag2_search.py"
RELATED_LIMIT = 2


def run_stage_rag2(query: list[str], top: int, window: int, preview: int) -> list[dict[str, Any]]:
    cmd = [
        sys.executable,
        str(STAGE_RAG2_SEARCH),
        "--json",
        "--top",
        str(top),
        "--window",
        str(window),
        "--preview-lines",
        str(preview),
    ]
    cmd += query
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    stdout = proc.stdout
    start = stdout.find("[")
    end = stdout.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Stage RAG-2 search did not emit JSON payload")
    return json.loads(stdout[start : end + 1])


def related_candidates(path: str) -> list[str]:
    rel = Path(path)
    base = rel.stem
    parent = (REPO_ROOT / rel).parent
    if not parent.exists():
        return []
    candidates: list[str] = []
    for sibling in sorted(parent.glob(f"{base}*")):
        if sibling == (REPO_ROOT / rel) or not sibling.is_file():
            continue
        repo_rel = sibling.relative_to(REPO_ROOT).as_posix()
        candidates.append(repo_rel)
        if len(candidates) >= RELATED_LIMIT:
            break
    return candidates


def preview_file(path: str, window: int) -> str:
    abspath = REPO_ROOT / path
    try:
        lines = abspath.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[:window])


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-3 hybrid retriever")
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("query", nargs="+")
    args = parser.parse_args()

    base_results = run_stage_rag2(args.query, args.top, args.window, args.preview_lines)
    enriched: list[dict[str, Any]] = []
    for result in base_results:
        entry = dict(result)
        entry["related"] = []
        for candidate in related_candidates(entry["path"]):
            entry["related"].append(
                {
                    "path": candidate,
                    "preview": preview_file(candidate, args.preview_lines),
                }
            )
        enriched.append(entry)

    payload = {
        "query": " ".join(args.query),
        "base_top": args.top,
        "results": enriched,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
