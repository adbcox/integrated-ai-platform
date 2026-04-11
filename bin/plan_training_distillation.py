#!/usr/bin/env python3
"""Build a lightweight training/distillation planning package from escalation captures."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_OUTCOMES = {"pass", "partial", "fail"}


@dataclass
class Decision:
    task_id: str
    decision: str
    reason: str
    summary_path: str
    record: dict[str, Any]


def _parse_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _normalize_outcome(raw: str) -> str:
    value = (raw or "").strip().lower()
    if value in ALLOWED_OUTCOMES:
        return value
    if "pass" in value:
        return "pass"
    if "fail" in value:
        return "fail"
    return "partial"


def _is_placeholder_text(value: str) -> bool:
    text = (value or "").strip().lower()
    return "<item>" in text or text in {"", "tbd", "todo", "unknown"}


def _load_summary_records(escalation_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    for summary_path in sorted(escalation_root.glob("*/summary.json")):
        data = _parse_json(summary_path)
        if not data:
            continue
        rows.append((summary_path, data))
    return rows


def _record_to_export(summary_path: Path, data: dict[str, Any]) -> dict[str, Any]:
    constraints = data.get("constraints")
    if isinstance(constraints, str):
        constraints_list = [constraints]
    elif isinstance(constraints, list):
        constraints_list = [str(x) for x in constraints]
    else:
        constraints_list = []

    commands = data.get("commands_tests_run")
    if isinstance(commands, list):
        commands_list = [str(x) for x in commands]
    else:
        commands_list = []

    return {
        "schema_version": "1",
        "record_id": str(data.get("task_id") or summary_path.parent.name),
        "timestamp_utc": str(data.get("timestamp_utc") or ""),
        "repo": str(data.get("repo") or "unknown"),
        "branch": str(data.get("branch") or "unknown"),
        "workflow_mode": str(data.get("workflow_mode") or "unknown"),
        "task_class": f"{str(data.get('escalation_trigger') or 'unknown')} | {str(data.get('fix_pattern_root_cause') or 'unknown')}",
        "instruction": str(data.get("problem_statement") or ""),
        "context": {
            "constraints": constraints_list,
            "codex_plan_summary": str(data.get("codex_plan_summary") or ""),
            "commands_tests_run": commands_list,
            "escalation_trigger": str(data.get("escalation_trigger") or "unknown"),
            "fix_pattern_root_cause": str(data.get("fix_pattern_root_cause") or "unknown"),
        },
        "target": {
            "completion_summary": str(data.get("completion_summary") or ""),
            "reusable_local_first_heuristic": str(data.get("reusable_local_first_heuristic") or ""),
            "outcome": _normalize_outcome(str(data.get("pass_fail_outcomes") or "partial")),
        },
        "source": {
            "summary_json": str(summary_path),
            "timeline_log": str(summary_path.parent / "timeline.log"),
            "patch_notes": str(summary_path.parent / "patch-notes.md"),
        },
    }


def _decide(summary_path: Path, data: dict[str, Any]) -> Decision:
    export = _record_to_export(summary_path, data)

    if export["workflow_mode"] == "tactical":
        return Decision(export["record_id"], "excluded", "non-escalated tactical record", str(summary_path), export)

    if not export["instruction"]:
        return Decision(export["record_id"], "excluded", "missing problem statement", str(summary_path), export)

    if not export["target"]["completion_summary"]:
        return Decision(export["record_id"], "needs-review", "missing completion summary", str(summary_path), export)

    if _is_placeholder_text(str(data.get("outcome_notes") or "")):
        return Decision(export["record_id"], "needs-review", "placeholder outcome notes", str(summary_path), export)

    if _is_placeholder_text(export["target"]["completion_summary"]):
        return Decision(export["record_id"], "needs-review", "placeholder completion summary", str(summary_path), export)

    if len(export["context"]["commands_tests_run"]) == 0:
        return Decision(export["record_id"], "needs-review", "missing commands/tests trace", str(summary_path), export)

    outcome = export["target"]["outcome"]
    if outcome == "fail":
        return Decision(export["record_id"], "excluded", "failed outcome not suitable for direct target", str(summary_path), export)

    if len(export["target"]["reusable_local_first_heuristic"].strip()) < 12:
        return Decision(export["record_id"], "needs-review", "weak reusable heuristic", str(summary_path), export)

    return Decision(export["record_id"], "candidate", "meets minimum curation rules", str(summary_path), export)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=True) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _build_summary(now_utc: str, escalation_root: Path, decisions: list[Decision], out_dir: Path) -> dict[str, Any]:
    by_decision = Counter(d.decision for d in decisions)
    by_reason = Counter(d.reason for d in decisions)
    by_mode = Counter(d.record.get("workflow_mode", "unknown") for d in decisions)
    by_class = Counter(d.record.get("task_class", "unknown") for d in decisions)

    candidates = [d for d in decisions if d.decision == "candidate"]
    readiness = {
        "record_count": len(candidates),
        "prompt_rule_tuning": "ready" if len(candidates) >= 1 else "not-ready",
        "retrieval_seed_set": "ready" if len(candidates) >= 3 else "not-ready",
        "sft_distillation_seed": "ready" if len(candidates) >= 10 else "not-ready",
    }

    summary = {
        "generated_at_utc": now_utc,
        "escalation_root": str(escalation_root),
        "planning_out_dir": str(out_dir),
        "records_total": len(decisions),
        "counts": {
            "candidate": by_decision.get("candidate", 0),
            "needs_review": by_decision.get("needs-review", 0),
            "excluded": by_decision.get("excluded", 0),
        },
        "decision_reasons": dict(by_reason),
        "by_workflow_mode": dict(by_mode),
        "top_task_classes": [
            {"task_class": cls, "count": count}
            for cls, count in by_class.most_common(10)
        ],
        "readiness": readiness,
        "outputs": {
            "candidate_manifest_jsonl": str(out_dir / "training-candidates.jsonl"),
            "needs_review_manifest_jsonl": str(out_dir / "needs-review.jsonl"),
            "excluded_manifest_jsonl": str(out_dir / "excluded.jsonl"),
            "latest_json": str(out_dir / "latest.json"),
            "latest_md": str(out_dir / "latest.md"),
        },
    }
    return summary


def _summary_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Training/Distillation Planning Summary")
    lines.append("")
    lines.append(f"- generated_at_utc: {summary['generated_at_utc']}")
    lines.append(f"- escalation_root: {summary['escalation_root']}")
    lines.append(f"- records_total: {summary['records_total']}")
    lines.append(f"- candidate: {summary['counts']['candidate']}")
    lines.append(f"- needs_review: {summary['counts']['needs_review']}")
    lines.append(f"- excluded: {summary['counts']['excluded']}")
    lines.append("")
    lines.append("## Readiness")
    readiness = summary["readiness"]
    lines.append(f"- prompt_rule_tuning: {readiness['prompt_rule_tuning']}")
    lines.append(f"- retrieval_seed_set: {readiness['retrieval_seed_set']}")
    lines.append(f"- sft_distillation_seed: {readiness['sft_distillation_seed']}")
    lines.append("")
    lines.append("## Decision Reasons")
    if not summary["decision_reasons"]:
        lines.append("- none")
    else:
        for reason, count in sorted(summary["decision_reasons"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {reason}: {count}")
    lines.append("")
    lines.append("## Top Task Classes")
    if not summary["top_task_classes"]:
        lines.append("- none")
    else:
        for item in summary["top_task_classes"]:
            lines.append(f"- {item['task_class']}: {item['count']}")
    lines.append("")
    lines.append("## Output Files")
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_escalation_root = Path(os.environ.get("ESCALATION_ROOT", str(base_dir / "artifacts" / "escalations")))
    default_out_dir = Path(os.environ.get("TRAIN_PLAN_OUT_DIR", str(base_dir / "artifacts" / "training-planning")))

    parser = argparse.ArgumentParser(description="Plan training/distillation candidates from escalation captures.")
    parser.add_argument("--escalation-root", default=str(default_escalation_root), help="Escalation artifact root")
    parser.add_argument("--out-dir", default=str(default_out_dir), help="Output planning directory")
    parser.add_argument("--write-plan", action="store_true", help="Write planning files to out-dir")
    parser.add_argument("--json-only", action="store_true", help="Print JSON summary instead of markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    escalation_root = Path(args.escalation_root).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not escalation_root.exists():
        print(f"No escalation root found: {escalation_root}")
        return 0

    rows = _load_summary_records(escalation_root)
    decisions = [_decide(path, data) for path, data in rows]

    candidates = [
        {
            "task_id": d.task_id,
            "reason": d.reason,
            "record": d.record,
        }
        for d in decisions
        if d.decision == "candidate"
    ]
    needs_review = [
        {
            "task_id": d.task_id,
            "reason": d.reason,
            "record": d.record,
        }
        for d in decisions
        if d.decision == "needs-review"
    ]
    excluded = [
        {
            "task_id": d.task_id,
            "reason": d.reason,
            "record": d.record,
        }
        for d in decisions
        if d.decision == "excluded"
    ]

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = _build_summary(now_utc, escalation_root, decisions, out_dir)
    markdown = _summary_markdown(summary)

    if args.write_plan:
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        _write_jsonl(out_dir / "training-candidates.jsonl", candidates)
        _write_jsonl(out_dir / "needs-review.jsonl", needs_review)
        _write_jsonl(out_dir / "excluded.jsonl", excluded)
        (out_dir / "latest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        (out_dir / "latest.md").write_text(markdown + "\n", encoding="utf-8")
        (out_dir / f"summary_{ts}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        (out_dir / f"summary_{ts}.md").write_text(markdown + "\n", encoding="utf-8")

    if args.json_only:
        print(json.dumps(summary, indent=2))
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
