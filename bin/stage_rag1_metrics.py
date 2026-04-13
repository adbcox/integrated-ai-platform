#!/usr/bin/env python3
"""Summarize Stage RAG-1 usage vs. guard failure types.

The script scans artifacts/stage_rag1/usage.jsonl for planning events and
artifacts/aider_runs/**/metadata.json for aide guard outcomes. It focuses on the
three failure signatures we care about for Stage-4 rollout:

* literal_replace_missing_old
* missing_file_ref
* missing_anchor
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


def load_usage(path: Path) -> list[dict]:
    events = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def iter_metadata(root: Path) -> Iterable[dict]:
    if not root.exists():
        return
    for meta in root.rglob("metadata.json"):
        try:
            text = meta.read_text()
        except OSError:
            continue
        if not text.strip():
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        yield data


def summarize_failures(metadata: list[dict], window: int) -> dict:
    focus = Counter()
    total = 0
    recent = sorted(metadata, key=lambda d: d.get("start_time", ""))[-window:]
    for data in recent:
        total += 1
        for sig in data.get("failure_signatures", []) or []:
            if sig in {"literal_replace_missing_old", "missing_file_ref", "missing_anchor"}:
                focus[sig] += 1
    return {"total_runs": total, "failures": dict(focus)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-1 rollout metrics")
    parser.add_argument("--usage-log", default="artifacts/stage_rag1/usage.jsonl")
    parser.add_argument("--runs-root", default="artifacts/aider_runs")
    parser.add_argument("--window", type=int, default=50, help="number of runs to scan")
    args = parser.parse_args()

    usage = load_usage(Path(args.usage_log))
    metadata = list(iter_metadata(Path(args.runs_root)))
    summary = summarize_failures(metadata, args.window)

    print("Stage RAG-1 planning events:")
    stages = Counter(event.get("stage", "unknown") for event in usage)
    for stage, count in sorted(stages.items()):
        print(f"  {stage}: {count}")
    print(f"  total logged events: {len(usage)}")

    print("\nGuard failure focus (last {window} runs):".format(window=summary["total_runs"]))
    for key in ["literal_replace_missing_old", "missing_file_ref", "missing_anchor"]:
        value = summary["failures"].get(key, 0)
        rate = (value / summary["total_runs"]) if summary["total_runs"] else 0.0
        print(f"  {key}: {value} ({rate:.2%})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
