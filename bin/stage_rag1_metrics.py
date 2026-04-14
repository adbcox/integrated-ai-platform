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
from pathlib import Path
from typing import Iterable

FOCUS_PREFAIL = [
    "literal_replace_missing_old",
    "literal_shell_risky",
    "prompt_contract_rejection",
    "missing_file_ref",
    "missing_anchor",
]


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


def load_events(path: Path) -> list[dict]:
    events: list[dict] = []
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


def summarize_preflight_events(events: list[dict]) -> dict:
    totals = Counter()
    focus = Counter()
    for event in events:
        phase = event.get("phase")
        status = event.get("status")
        tag = event.get("tag")
        if phase == "preflight":
            totals["preflight_total"] += 1
            if status == "failure" and tag in FOCUS_PREFAIL:
                focus[tag] += 1
        if status == "success":
            totals["success"] += 1
        if status == "failure":
            totals["failure"] += 1
    return {"totals": dict(totals), "focus": dict(focus)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-1 rollout metrics")
    parser.add_argument("--usage-log", default="artifacts/stage_rag1/usage.jsonl")
    parser.add_argument("--runs-root", default="artifacts/aider_runs")
    parser.add_argument("--window", type=int, default=50, help="number of runs to scan")
    parser.add_argument(
        "--micro-events",
        default="artifacts/micro_runs/events.jsonl",
        help="event log emitted by bin/aider_micro.sh",
    )
    args = parser.parse_args()

    usage = load_usage(Path(args.usage_log))
    metadata = list(iter_metadata(Path(args.runs_root)))
    micro_events = load_events(Path(args.micro_events))
    summary = summarize_failures(metadata, args.window)
    preflight = summarize_preflight_events(micro_events)

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

    print("\nMicro-lane preflight rejections (from artifacts/micro_runs/events.jsonl):")
    total_pre = preflight["totals"].get("preflight_total", 0)
    for key in FOCUS_PREFAIL:
        count = preflight["focus"].get(key, 0)
        rate = (count / total_pre) if total_pre else 0.0
        print(f"  {key}: {count} ({rate:.2%})")
    print(
        "  successes vs. failures: {success}/{failure}".format(
            success=preflight["totals"].get("success", 0),
            failure=preflight["totals"].get("failure", 0),
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
