#!/usr/bin/env python3
"""Assess whether a candidate class has enough real evidence for heuristic validation."""
from __future__ import annotations

import argparse  # stage7-op
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Evidence:
    task_id: str
    summary_path: Path
    has_placeholders: bool
    missing_context: bool
    workflow_mode: str
    commands: list[str]
    notes: dict[str, Any]


PLACEHOLDER_TOKENS = {"<item>", "<goal>", "<problem>", "<summary>", "<what was changed and why>"}
FIELD_KEYS = (
    "problem_statement",
    "completion_summary",
    "outcome_notes",
    "reusable_local_first_heuristic",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assess candidate class evidence from escalation artifacts.")
    parser.add_argument("--class", dest="class_name", default="", help="Class key '<trigger> | <fix_pattern>'")
    parser.add_argument("--trigger", default="", help="Trigger name")
    parser.add_argument("--fix-pattern", default="", help="Fix/root-cause pattern")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent / "artifacts" / "escalations"), help="Escalation root")
    return parser.parse_args()


def resolve_class(args: argparse.Namespace) -> str:
    if args.class_name.strip():
        return args.class_name.strip()
    if args.trigger.strip() and args.fix_pattern.strip():
        return f"{args.trigger.strip()} | {args.fix_pattern.strip()}"
    raise SystemExit("ERROR: must provide --class or both --trigger and --fix-pattern")


def load_summaries(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    if not root.is_dir():
        return rows
    for summary_path in sorted(root.glob("*/summary.json")):
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append((summary_path, data))
    return rows


def is_placeholder_text(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return True
    lowered = text.lower()
    if "<" in text and ">" in text:
        return True
    return lowered in PLACEHOLDER_TOKENS


def classify_evidence(summary_path: Path, data: dict[str, Any]) -> Evidence:
    placeholders = False
    for key in FIELD_KEYS:
        if is_placeholder_text(str(data.get(key, ""))):
            placeholders = True
            break
    commands = data.get("commands_tests_run")
    cmd_list = [str(x) for x in commands] if isinstance(commands, list) else []
    missing_context = len(cmd_list) == 0
    return Evidence(
        task_id=str(data.get("task_id") or summary_path.parent.name),
        summary_path=summary_path,
        has_placeholders=placeholders,
        missing_context=missing_context,
        workflow_mode=str(data.get("workflow_mode") or "unknown"),
        commands=cmd_list,
        notes={
            "completion_summary": data.get("completion_summary"),
            "outcome_notes": data.get("outcome_notes"),
        },
    )


def summarize(evidence: list[Evidence]) -> None:
    valid = [ev for ev in evidence if not ev.has_placeholders and not ev.missing_context]
    state = "insufficient evidence"
    if len(valid) >= 2:
        state = "ready for bounded validation recommendation"
    elif len(valid) == 1:
        state = "plausibility assessment"

    print(f"State: {state}")
    print(f"Total matching runs: {len(evidence)} (valid: {len(valid)})")
    if evidence:
        print("")
        print("Details:")
        for ev in evidence:
            issues = []
            if ev.has_placeholders:
                issues.append("placeholder fields")
            if ev.missing_context:
                issues.append("missing commands/log context")
            issue_text = ", ".join(issues) if issues else "ok"
            print(f"- {ev.task_id}: mode={ev.workflow_mode} issues={issue_text} summary={ev.summary_path}")

    print("")
    if state == "insufficient evidence":
        print("Action: run at least one real task for this class and ensure capture fields are filled.")
    elif state == "plausibility assessment":
        print("Action: gather one more clean run before starting bounded validation.")
    else:
        print("Action: enough evidence for a bounded validation proposal; proceed with the standard cycle if desired.")


def main() -> int:
    args = parse_args()
    class_key = resolve_class(args)
    root = Path(args.root).resolve()
    summaries = load_summaries(root)

    matching: list[Evidence] = []
    for summary_path, data in summaries:
        trigger = str(data.get("escalation_trigger") or "unknown")
        fix_pattern = str(data.get("fix_pattern_root_cause") or "unknown")
        class_name = f"{trigger} | {fix_pattern}"
        if class_name == class_key:
            matching.append(classify_evidence(summary_path, data))

    if not matching:
        print("State: insufficient evidence")
        print("Reason: no escalation summaries found for class '" + class_key + "'.")
        print("Action: capture at least one real run before assessment.")
        return 0

    summarize(matching)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
