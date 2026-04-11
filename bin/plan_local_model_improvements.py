#!/usr/bin/env python3
"""Generate a lightweight local-model improvement plan from escalation artifacts."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Record:
    task_id: str
    workflow_mode: str
    escalation_trigger: str
    fix_pattern: str
    outcome: str
    heuristic: str


def normalize_outcome(value: str) -> str:
    v = (value or "").strip().lower()
    if v in {"pass", "partial", "fail"}:
        return v
    if "pass" in v:
        return "pass"
    if "fail" in v:
        return "fail"
    return "partial"


def load_records(escalation_root: Path) -> list[Record]:
    records: list[Record] = []
    for summary in sorted(escalation_root.glob("*/summary.json")):
        try:
            data = json.loads(summary.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records.append(
            Record(
                task_id=str(data.get("task_id") or summary.parent.name),
                workflow_mode=str(data.get("workflow_mode") or "unknown"),
                escalation_trigger=str(data.get("escalation_trigger") or "unknown"),
                fix_pattern=str(data.get("fix_pattern_root_cause") or "unknown"),
                outcome=normalize_outcome(str(data.get("pass_fail_outcomes") or "partial")),
                heuristic=str(data.get("reusable_local_first_heuristic") or ""),
            )
        )
    return records


def classify_class(
    trigger: str,
    total: int,
    passed: int,
    partial: int,
    failed: int,
) -> tuple[str, str]:
    fail_rate = failed / total if total else 0.0

    # Local-first needs stronger evidence.
    if total >= 3 and fail_rate <= 0.10 and passed >= 2:
        return "local-first candidate", "stable multi-sample success profile"

    # Immediate hard-failure classes stay Codex-heavy for now.
    if (fail_rate >= 0.50 and total >= 2) or (
        trigger == "hard-failure-analysis" and passed == 0 and total >= 2
    ):
        return "codex-required for now", "high failure pressure or repeated hard-failure class"

    # Assist tier: low observed failure but still limited/partial evidence.
    if fail_rate <= 0.25 and (passed + partial) >= 1:
        return "local-with-codex-assist", "low observed failure with incomplete confidence"

    return "codex-preferred", "insufficient local stability evidence"


def mode_recommendation(category: str) -> str:
    return {
        "local-first candidate": "tactical",
        "local-with-codex-assist": "codex-assist",
        "codex-preferred": "codex-investigate",
        "codex-required for now": "codex-failure",
    }[category]


def build_plan(records: list[Record], escalation_root: Path) -> dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    class_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "total": 0,
        "pass": 0,
        "partial": 0,
        "fail": 0,
        "trigger": "unknown",
        "fix_pattern": "unknown",
        "workflow_modes": Counter(),
        "heuristics": Counter(),
    })

    for r in records:
        cls = f"{r.escalation_trigger} | {r.fix_pattern}"
        s = class_stats[cls]
        s["total"] += 1
        s[r.outcome] += 1
        s["trigger"] = r.escalation_trigger
        s["fix_pattern"] = r.fix_pattern
        s["workflow_modes"][r.workflow_mode] += 1
        if r.heuristic:
            s["heuristics"][r.heuristic] += 1

    categorized: dict[str, list[dict[str, Any]]] = {
        "local-first candidate": [],
        "local-with-codex-assist": [],
        "codex-preferred": [],
        "codex-required for now": [],
    }

    for cls, s in class_stats.items():
        category, reason = classify_class(
            s["trigger"], s["total"], s["pass"], s["partial"], s["fail"]
        )
        top_heuristic = ""
        if s["heuristics"]:
            top_heuristic = s["heuristics"].most_common(1)[0][0]
        item = {
            "class": cls,
            "trigger": s["trigger"],
            "fix_pattern": s["fix_pattern"],
            "total": s["total"],
            "pass": s["pass"],
            "partial": s["partial"],
            "fail": s["fail"],
            "reason": reason,
            "recommended_workflow_mode": mode_recommendation(category),
            "candidate_heuristic": top_heuristic,
            "workflow_modes_seen": dict(s["workflow_modes"]),
        }
        categorized[category].append(item)

    for key in categorized:
        categorized[key].sort(key=lambda x: (x["fail"], -x["pass"], -x["total"]), reverse=True)

    # Prioritized planning actions for the next cycle.
    actions: list[dict[str, str]] = []

    for item in categorized["local-first candidate"][:3]:
        actions.append(
            {
                "action": f"Promote class to local-first default: {item['class']}",
                "mode": "tactical",
                "why": item["reason"],
            }
        )

    for item in categorized["local-with-codex-assist"][:3]:
        actions.append(
            {
                "action": f"Add local decomposition heuristic + assist fallback: {item['class']}",
                "mode": "codex-assist",
                "why": item["reason"],
            }
        )

    for item in categorized["codex-preferred"][:3]:
        actions.append(
            {
                "action": f"Keep Codex investigate default while collecting more local evidence: {item['class']}",
                "mode": "codex-investigate",
                "why": item["reason"],
            }
        )

    for item in categorized["codex-required for now"][:3]:
        actions.append(
            {
                "action": f"Preserve Codex failure-mode default; focus on root-cause templates: {item['class']}",
                "mode": "codex-failure",
                "why": item["reason"],
            }
        )

    threshold_policy = {
        "local-first candidate": "total>=3, fail_rate<=0.10, pass>=2",
        "local-with-codex-assist": "fail_rate<=0.25 with at least one successful/partial sample",
        "codex-preferred": "default when evidence is limited or local stability is unclear",
        "codex-required for now": "fail_rate>=0.50 with >=2 samples OR repeated hard-failure class with no pass",
    }

    plan = {
        "generated_at_utc": now,
        "escalation_root": str(escalation_root),
        "records_total": len(records),
        "decision_framework": threshold_policy,
        "categorized_task_classes": categorized,
        "next_cycle_actions": actions,
    }
    return plan


def plan_to_markdown(plan: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Local-Model Improvement Plan")
    lines.append("")
    lines.append(f"- generated_at_utc: {plan['generated_at_utc']}")
    lines.append(f"- escalation_root: {plan['escalation_root']}")
    lines.append(f"- records_total: {plan['records_total']}")
    lines.append("")

    lines.append("## Decision Framework")
    for k, v in plan["decision_framework"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    for cat in [
        "local-first candidate",
        "local-with-codex-assist",
        "codex-preferred",
        "codex-required for now",
    ]:
        lines.append(f"## {cat.title()}")
        items = plan["categorized_task_classes"].get(cat, [])
        if not items:
            lines.append("- none")
            lines.append("")
            continue
        for item in items[:10]:
            lines.append(
                "- "
                + f"{item['class']}: total={item['total']} pass={item['pass']} partial={item['partial']} fail={item['fail']} "
                + f"mode={item['recommended_workflow_mode']} reason={item['reason']}"
            )
            if item.get("candidate_heuristic"):
                lines.append(f"  heuristic: {item['candidate_heuristic']}")
        lines.append("")

    lines.append("## Next-Cycle Actions")
    actions = plan.get("next_cycle_actions", [])
    if not actions:
        lines.append("- none")
    else:
        for a in actions:
            lines.append(f"- {a['action']} (mode={a['mode']}; why={a['why']})")
    lines.append("")

    lines.append("## Operator Use")
    lines.append("- Run `make local-model-eval` before planning.")
    lines.append("- Run `make local-model-plan` to refresh task-class recommendations.")
    lines.append("- Apply at most 1-2 heuristic/rule updates per cycle, then re-measure.")
    lines.append("")

    return "\n".join(lines)


def write_outputs(out_dir: Path, plan: dict[str, Any], markdown: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    (out_dir / "latest.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (out_dir / f"plan_{ts}.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (out_dir / "latest.md").write_text(markdown + "\n", encoding="utf-8")
    (out_dir / f"plan_{ts}.md").write_text(markdown + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_escalation_root = Path(os.environ.get("ESCALATION_ROOT", str(base_dir / "artifacts" / "escalations")))
    default_out_dir = Path(os.environ.get("PLAN_OUT_DIR", str(base_dir / "artifacts" / "planning")))

    parser = argparse.ArgumentParser(description="Generate a local-model improvement plan from escalation captures.")
    parser.add_argument("--escalation-root", default=str(default_escalation_root), help="Escalation artifact root")
    parser.add_argument("--out-dir", default=str(default_out_dir), help="Output plan directory")
    parser.add_argument("--write-plan", action="store_true", help="Write plan files to out-dir")
    parser.add_argument("--json-only", action="store_true", help="Print JSON plan instead of markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    escalation_root = Path(args.escalation_root).resolve()
    if not escalation_root.exists():
        print(f"No escalation root found: {escalation_root}")
        return 0

    records = load_records(escalation_root)
    plan = build_plan(records, escalation_root)
    markdown = plan_to_markdown(plan)

    if args.write_plan:
        write_outputs(Path(args.out_dir).resolve(), plan, markdown)

    if args.json_only:
        print(json.dumps(plan, indent=2))
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
