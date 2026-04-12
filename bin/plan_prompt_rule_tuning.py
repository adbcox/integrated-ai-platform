#!/usr/bin/env python3
"""Generate prompt/rule tuning guidance from training-plan outputs."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PromptSeed:
    task_id: str
    task_class: str
    workflow_mode: str
    heuristic: str
    prompt_snippet: str
    summary_path: str


@dataclass
class ReviewAction:
    task_id: str
    reason: str
    action_hint: str
    summary_path: str


ACTION_HINTS = {
    "placeholder outcome notes": "Rewrite the outcome/summary text in the escalation summary so it reflects the actual result, then rerun `make local-model-train-plan`.",
    "missing completion summary": "Populate `completion_summary` in the escalation summary to describe what changed before rerunning `make local-model-train-plan`.",
    "missing commands/tests trace": "Record the commands/tests executed in the summary file under `commands_tests_run`, then refresh the training plan.",
    "weak reusable heuristic": "Expand `reusable_local_first_heuristic` with a concrete operator action (>=12 chars) and refresh the training plan.",
}


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_training_dir = Path(os.environ.get("TRAIN_PLAN_OUT_DIR", base_dir / "artifacts" / "training-planning"))
    default_out_dir = Path(os.environ.get("PROMPT_RULE_OUT_DIR", base_dir / "artifacts" / "prompt-rule-tuning"))

    parser = argparse.ArgumentParser(description="Build prompt/rule tuning guidance from curated training inputs.")
    parser.add_argument("--training-plan-dir", default=str(default_training_dir), help="Directory containing training plan jsonl outputs")
    parser.add_argument("--out-dir", default=str(default_out_dir), help="Output directory for prompt/rule guidance")
    parser.add_argument("--json-only", action="store_true", help="Print JSON summary to stdout")
    parser.add_argument("--write-plan", action="store_true", help="Write artifacts under the output directory")
    return parser.parse_args()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def _build_prompt_seed(row: dict[str, Any]) -> PromptSeed:
    record = row.get("record", {})
    task_id = str(row.get("task_id") or record.get("record_id") or "unknown")
    task_class = str(record.get("task_class") or "unknown")
    workflow_mode = str(record.get("workflow_mode") or "unknown")
    heuristic = str(record.get("target", {}).get("reusable_local_first_heuristic") or "").strip()
    instruction = str(record.get("instruction") or "")
    commands = _safe_list(record.get("context", {}).get("commands_tests_run"))
    cmd_text = ", ".join(commands) if commands else "(not captured)"
    prompt_lines = [
        f"Task class: {task_class}",
        f"Instruction: {instruction or 'n/a'}",
        f"Workflow mode used: {workflow_mode}",
        f"Commands/tests captured: {cmd_text}",
    ]
    if heuristic:
        prompt_lines.append(f"Reusable heuristic: {heuristic}")
    summary_path = str(record.get("source", {}).get("summary_json") or "")
    return PromptSeed(
        task_id=task_id,
        task_class=task_class,
        workflow_mode=workflow_mode,
        heuristic=heuristic,
        prompt_snippet="\n".join(prompt_lines),
        summary_path=summary_path,
    )


def _build_review_action(row: dict[str, Any]) -> ReviewAction:
    record = row.get("record", {})
    task_id = str(row.get("task_id") or record.get("record_id") or "unknown")
    reason = str(row.get("reason") or "needs-review")
    hint = ACTION_HINTS.get(reason.lower(), "Update the escalation summary to resolve this gap, then rerun `make local-model-train-plan`.")
    summary_path = str(record.get("source", {}).get("summary_json") or "")
    return ReviewAction(task_id=task_id, reason=reason, action_hint=hint, summary_path=summary_path)


def build_report(training_dir: Path, out_dir: Path) -> dict[str, Any]:
    candidates_path = training_dir / "training-candidates.jsonl"
    needs_review_path = training_dir / "needs-review.jsonl"

    candidate_rows = _load_jsonl(candidates_path)
    review_rows = _load_jsonl(needs_review_path)

    prompt_seeds = [_build_prompt_seed(row) for row in candidate_rows]
    review_actions = [_build_review_action(row) for row in review_rows]

    status = "ready" if prompt_seeds else "blocked-needs-review"
    status_reason = "candidates>=1" if prompt_seeds else "no curated prompt seeds yet"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    report = {
        "generated_at_utc": now,
        "training_plan_dir": str(training_dir),
        "output_dir": str(out_dir),
        "status": status,
        "status_reason": status_reason,
        "counts": {
            "prompt_seeds": len(prompt_seeds),
            "needs_review": len(review_actions),
        },
        "prompt_seeds": [seed.__dict__ for seed in prompt_seeds],
        "needs_review_actions": [action.__dict__ for action in review_actions],
        "operator_next_steps": _next_steps(prompt_seeds, review_actions),
    }
    return report


def _next_steps(prompt_seeds: list[PromptSeed], review_actions: list[ReviewAction]) -> list[str]:
    steps: list[str] = []
    if prompt_seeds:
        steps.append("Integrate the prompt snippets below into local developer prompts or routing rules for the matching task classes.")
    else:
        steps.append("Resolve needs-review items so at least one curated prompt seed exists, then regenerate this report.")
    if review_actions:
        steps.append("Open each listed summary.json path, address the noted reason, and rerun `make local-model-train-plan`.")
    steps.append("After updating prompts/rules, rerun `make local-model-rules-refresh` if routing heuristics changed.")
    return steps


def write_report(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "latest.json"
    latest_md = out_dir / "latest.md"
    snapshot_json = out_dir / f"summary_{timestamp}.json"
    snapshot_md = out_dir / f"summary_{timestamp}.md"

    json_blob = json.dumps(report, indent=2) + "\n"
    latest_json.write_text(json_blob, encoding="utf-8")
    snapshot_json.write_text(json_blob, encoding="utf-8")

    md_blob = _markdown(report)
    latest_md.write_text(md_blob, encoding="utf-8")
    snapshot_md.write_text(md_blob, encoding="utf-8")

    print(f"Wrote prompt/rule guidance: {latest_md}")


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Prompt/Rule Tuning Guidance")
    lines.append("")
    lines.append(f"- generated_at_utc: {report['generated_at_utc']}")
    lines.append(f"- training_plan_dir: {report['training_plan_dir']}")
    lines.append(f"- status: {report['status']} ({report['status_reason']})")
    lines.append(f"- prompt_seeds: {report['counts']['prompt_seeds']}")
    lines.append(f"- needs_review: {report['counts']['needs_review']}")
    lines.append("")
    lines.append("## Operator Next Steps")
    for step in report["operator_next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("## Prompt Seeds")
    if not report["prompt_seeds"]:
        lines.append("- None yet. Resolve needs-review items to unlock candidates.")
    else:
        for seed in report["prompt_seeds"]:
            lines.append(f"- **{seed['task_id']}** ({seed['task_class']})")
            lines.append(f"  - workflow_mode: {seed['workflow_mode']}")
            if seed.get("heuristic"):
                lines.append(f"  - heuristic: {seed['heuristic']}")
            if seed.get("summary_path"):
                lines.append(f"  - summary: {seed['summary_path']}")
            lines.append("  - prompt_snippet:")
            for snippet_line in seed["prompt_snippet"].splitlines():
                lines.append(f"    {snippet_line}")
            lines.append("")
    lines.append("## Needs-Review Actions")
    if not report["needs_review_actions"]:
        lines.append("- None")
    else:
        for action in report["needs_review_actions"]:
            lines.append(f"- **{action['task_id']}**")
            lines.append(f"  - reason: {action['reason']}")
            lines.append(f"  - action: {action['action_hint']}")
            if action.get("summary_path"):
                lines.append(f"  - summary: {action['summary_path']}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    training_dir = Path(args.training_plan_dir).resolve()
    out_dir = Path(args.out_dir).resolve()

    report = build_report(training_dir, out_dir)

    if args.write_plan:
        write_report(report, out_dir)

    if args.json_only:
        print(json.dumps(report, indent=2))
    else:
        print(_markdown(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

