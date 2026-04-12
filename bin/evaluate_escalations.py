#!/usr/bin/env python3
"""Lightweight local-model evaluation harness over Codex escalation artifacts."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_OUTCOMES = {"pass", "partial", "fail"}


@dataclass
class EscalationRecord:
    task_id: str
    timestamp_utc: str
    repo: str
    branch: str
    workflow_mode: str
    escalation_trigger: str
    pass_fail_outcomes: str
    fix_pattern_root_cause: str
    reusable_local_first_heuristic: str
    summary_json_path: str


def _normalize_outcome(raw: str) -> str:
    value = (raw or "").strip().lower()
    if value in VALID_OUTCOMES:
        return value
    if "pass" in value:
        return "pass"
    if "fail" in value:
        return "fail"
    return "partial"


def _parse_json_file(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_records(escalation_root: Path) -> list[EscalationRecord]:
    records_by_id: dict[str, EscalationRecord] = {}

    # Preferred source: summary.json files under task dirs.
    for summary_path in sorted(escalation_root.glob("*/summary.json")):
        data = _parse_json_file(summary_path)
        if not data:
            continue
        task_id = str(data.get("task_id") or summary_path.parent.name)
        rec = EscalationRecord(
            task_id=task_id,
            timestamp_utc=str(data.get("timestamp_utc") or ""),
            repo=str(data.get("repo") or "unknown"),
            branch=str(data.get("branch") or "unknown"),
            workflow_mode=str(data.get("workflow_mode") or "unknown"),
            escalation_trigger=str(data.get("escalation_trigger") or "unknown"),
            pass_fail_outcomes=_normalize_outcome(str(data.get("pass_fail_outcomes") or "partial")),
            fix_pattern_root_cause=str(data.get("fix_pattern_root_cause") or "unknown"),
            reusable_local_first_heuristic=str(data.get("reusable_local_first_heuristic") or ""),
            summary_json_path=str(summary_path),
        )
        records_by_id[task_id] = rec

    # Supplemental source: index.jsonl (fills gaps if summary file missing).
    index_path = escalation_root / "index.jsonl"
    if index_path.is_file():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            task_id = str(data.get("task_id") or "")
            if not task_id or task_id in records_by_id:
                continue
            rec = EscalationRecord(
                task_id=task_id,
                timestamp_utc=str(data.get("timestamp_utc") or ""),
                repo=str(data.get("repo") or "unknown"),
                branch=str(data.get("branch") or "unknown"),
                workflow_mode=str(data.get("workflow_mode") or "unknown"),
                escalation_trigger=str(data.get("escalation_trigger") or "unknown"),
                pass_fail_outcomes=_normalize_outcome(str(data.get("pass_fail_outcomes") or "partial")),
                fix_pattern_root_cause="unknown",
                reusable_local_first_heuristic="",
                summary_json_path=str(data.get("summary_json") or ""),
            )
            records_by_id[task_id] = rec

    return sorted(records_by_id.values(), key=lambda r: (r.timestamp_utc, r.task_id))


def classify_task_classes(records: list[EscalationRecord]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_class: dict[str, Counter[str]] = defaultdict(Counter)
    heuristics_by_class: dict[str, Counter[str]] = defaultdict(Counter)

    for rec in records:
        cls = f"{rec.escalation_trigger} | {rec.fix_pattern_root_cause}"
        by_class[cls]["total"] += 1
        by_class[cls][rec.pass_fail_outcomes] += 1
        if rec.reusable_local_first_heuristic:
            heuristics_by_class[cls][rec.reusable_local_first_heuristic] += 1

    local_first_candidates: list[dict[str, Any]] = []
    codex_preferred: list[dict[str, Any]] = []

    for cls, counts in by_class.items():
        total = counts["total"]
        passed = counts["pass"]
        partial = counts["partial"]
        failed = counts["fail"]
        fail_rate = failed / total if total else 0.0
        sample_heuristic = ""
        if heuristics_by_class[cls]:
            sample_heuristic = heuristics_by_class[cls].most_common(1)[0][0]

        row = {
            "class": cls,
            "total": total,
            "pass": passed,
            "partial": partial,
            "fail": failed,
            "fail_rate": round(fail_rate, 3),
            "sample_heuristic": sample_heuristic,
        }

        # Canonical local-first rule (aligned with planning/doc policy):
        # - local-first candidate: total>=3, fail_rate<=0.10, pass>=2
        # - Codex-preferred: any failures or explicitly failure-heavy class naming
        if total >= 3 and fail_rate <= 0.10 and passed >= 2:
            row["local_first_score"] = passed * 2 + partial
            local_first_candidates.append(row)
        if failed > 0 or cls.startswith("hard-failure-analysis"):
            row["codex_priority_score"] = failed * 2 + partial
            codex_preferred.append(row)

    local_first_candidates.sort(key=lambda x: (x.get("local_first_score", 0), x["total"]), reverse=True)
    codex_preferred.sort(key=lambda x: (x.get("codex_priority_score", 0), x["total"]), reverse=True)
    return local_first_candidates, codex_preferred


def build_report(records: list[EscalationRecord], escalation_root: Path) -> tuple[str, dict[str, Any]]:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    mode_counts = Counter(rec.workflow_mode for rec in records)
    trigger_counts = Counter(rec.escalation_trigger for rec in records)
    repo_counts = Counter(rec.repo for rec in records)
    outcome_counts = Counter(rec.pass_fail_outcomes for rec in records)
    pattern_counts = Counter(rec.fix_pattern_root_cause for rec in records)

    local_first_candidates, codex_preferred = classify_task_classes(records)

    summary = {
        "generated_at_utc": now_utc,
        "escalation_root": str(escalation_root),
        "records_total": len(records),
        "by_workflow_mode": dict(mode_counts),
        "by_escalation_trigger": dict(trigger_counts),
        "by_repo": dict(repo_counts),
        "by_outcome": dict(outcome_counts),
        "by_fix_pattern_root_cause": dict(pattern_counts),
        "local_first_candidates": local_first_candidates,
        "codex_preferred_classes": codex_preferred,
    }

    lines: list[str] = []
    lines.append("# Local-Model Evaluation Summary")
    lines.append("")
    lines.append(f"- generated_at_utc: {now_utc}")
    lines.append(f"- escalation_root: {escalation_root}")
    lines.append(f"- records_total: {len(records)}")
    lines.append("")

    def add_counter_section(title: str, counter: Counter[str]) -> None:
        lines.append(f"## {title}")
        if not counter:
            lines.append("- none")
        else:
            for key, value in counter.most_common():
                lines.append(f"- {key}: {value}")
        lines.append("")

    add_counter_section("By Workflow Mode", mode_counts)
    add_counter_section("By Escalation Trigger", trigger_counts)
    add_counter_section("By Repo", repo_counts)
    add_counter_section("By Outcome", outcome_counts)
    add_counter_section("By Fix/Root-Cause", pattern_counts)

    lines.append("## Local-First Candidate Classes")
    if not local_first_candidates:
        lines.append("- insufficient evidence yet")
    else:
        for row in local_first_candidates[:10]:
            lines.append(
                f"- {row['class']}: total={row['total']} pass={row['pass']} partial={row['partial']} fail={row['fail']} heuristic=\"{row['sample_heuristic'] or 'n/a'}\""
            )
    lines.append("")

    lines.append("## Codex-Preferred Classes")
    if not codex_preferred:
        lines.append("- no strong codex-preferred classes detected yet")
    else:
        for row in codex_preferred[:10]:
            lines.append(
                f"- {row['class']}: total={row['total']} pass={row['pass']} partial={row['partial']} fail={row['fail']}"
            )
    lines.append("")

    lines.append("## Immediate Local-Model Improvement Hints")
    if local_first_candidates:
        for row in local_first_candidates[:3]:
            lines.append(f"- Encode heuristic for local-first handling: {row['class']}")
    else:
        lines.append("- Capture more escalations with explicit fix-pattern + heuristic fields for stronger local-first candidate scoring.")
    if codex_preferred:
        for row in codex_preferred[:3]:
            lines.append(f"- Keep Codex escalation default for class: {row['class']}")
    else:
        lines.append("- No failure-heavy class yet; continue monitoring before narrowing Codex escalation defaults.")
    lines.append("")

    return "\n".join(lines), summary


def write_outputs(out_dir: Path, markdown_report: str, summary_json: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    latest_md = out_dir / "latest.md"
    latest_json = out_dir / "latest.json"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stamp_md = out_dir / f"summary_{ts}.md"
    stamp_json = out_dir / f"summary_{ts}.json"

    latest_md.write_text(markdown_report + "\n", encoding="utf-8")
    stamp_md.write_text(markdown_report + "\n", encoding="utf-8")
    latest_json.write_text(json.dumps(summary_json, indent=2) + "\n", encoding="utf-8")
    stamp_json.write_text(json.dumps(summary_json, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_escalation_root = Path(os.environ.get("ESCALATION_ROOT", str(base_dir / "artifacts" / "escalations")))
    default_out_dir = Path(os.environ.get("EVAL_OUT_DIR", str(base_dir / "artifacts" / "evaluation")))

    parser = argparse.ArgumentParser(description="Evaluate Codex escalation captures for local-model improvement planning.")
    parser.add_argument("--escalation-root", default=str(default_escalation_root), help="Escalation artifact root")
    parser.add_argument("--out-dir", default=str(default_out_dir), help="Output dir for reports")
    parser.add_argument("--write-report", action="store_true", help="Write markdown/json reports under out-dir")
    parser.add_argument("--json-only", action="store_true", help="Print summary JSON instead of markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    escalation_root = Path(args.escalation_root).resolve()
    if not escalation_root.exists():
        print(f"No escalation root found: {escalation_root}")
        return 0

    records = load_records(escalation_root)
    report_md, summary = build_report(records, escalation_root)

    if args.write_report:
        write_outputs(Path(args.out_dir).resolve(), report_md, summary)

    if args.json_only:
        print(json.dumps(summary, indent=2))
    else:
        print(report_md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
