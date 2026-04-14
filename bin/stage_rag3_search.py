#!/usr/bin/env python3
"""Stage RAG-3 hybrid retriever.

Extends Stage RAG-2 by pairing lexical/structural hits with nearby related files
and recently co-edited partners so Stage-5 multi-file batches can pre-select
anchors for both primary and secondary targets.
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
GIT_HISTORY_WINDOW = 15


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


def related_candidates(path: str, limit: int) -> list[str]:
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
        if len(candidates) >= limit:
            break
    return candidates


def git_recent_partners(path: str, history_window: int, limit: int) -> list[str]:
    """Return files that recently changed alongside `path`."""
    cmd = [
        "git",
        "-C",
        str(REPO_ROOT),
        "log",
        f"-n{history_window}",
        "--name-only",
        "--pretty=format:commit %H",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return []

    partners: list[str] = []
    seen: set[str] = set()
    target = path
    current_files: list[str] = []
    includes_target = False
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("commit "):
            if includes_target:
                for other in current_files:
                    if other == target or other in seen:
                        continue
                    seen.add(other)
                    partners.append(other)
                    if len(partners) >= limit:
                        return partners
            current_files = []
            includes_target = False
            continue
        current_files.append(line)
        if line == target:
            includes_target = True

    if includes_target:
        for other in current_files:
            if other == target or other in seen:
                continue
            partners.append(other)
            if len(partners) >= limit:
                break
    return partners


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
    parser.add_argument("--related-limit", type=int, default=RELATED_LIMIT, help="Sibling suggestions per hit")
    parser.add_argument(
        "--history-window",
        type=int,
        default=GIT_HISTORY_WINDOW,
        help="Git commit window for partner discovery",
    )
    parser.add_argument("query", nargs="+")
    args = parser.parse_args()

    base_results = run_stage_rag2(args.query, args.top, args.window, args.preview_lines)
    enriched: list[dict[str, Any]] = []
    for result in base_results:
        entry = dict(result)
        entry["related"] = []
        added_paths: set[str] = set()
        for candidate in related_candidates(entry["path"], max(0, args.related_limit)):
            entry["related"].append(
                {
                    "path": candidate,
                    "preview": preview_file(candidate, args.preview_lines),
                    "source": "sibling",
                }
            )
            added_paths.add(candidate)
        for partner in git_recent_partners(entry["path"], args.history_window, max(0, args.related_limit)):
            if partner in added_paths:
                continue
            entry["related"].append(
                {
                    "path": partner,
                    "preview": preview_file(partner, args.preview_lines),
                    "source": "git_history",
                }
            )
            added_paths.add(partner)
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
