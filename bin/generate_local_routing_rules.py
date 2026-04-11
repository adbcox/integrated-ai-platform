#!/usr/bin/env python3
"""Generate local behavior routing rules from local-model planning output."""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODE_RANK = {
    "tactical": 0,
    "codex-assist": 1,
    "codex-investigate": 2,
    "codex-failure": 3,
}


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_plan = Path(os.environ.get("PLAN_JSON", str(base_dir / "artifacts" / "planning" / "latest.json")))
    default_rules = Path(os.environ.get("RULES_FILE", str(base_dir / "policies" / "local-routing-rules.json")))

    parser = argparse.ArgumentParser(description="Generate local routing rules from planning output.")
    parser.add_argument("--plan-json", default=str(default_plan), help="Path to planning latest.json")
    parser.add_argument("--out-file", default=str(default_rules), help="Output routing policy file")
    parser.add_argument("--print", action="store_true", help="Print generated policy JSON")
    return parser.parse_args()


def load_plan(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Planning JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_more_conservative_mode(current: str, candidate: str) -> str:
    if MODE_RANK.get(candidate, -1) > MODE_RANK.get(current, -1):
        return candidate
    return current


def build_rules(plan: dict[str, Any], plan_path: Path) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    categorized = plan.get("categorized_task_classes", {})

    class_overrides: list[dict[str, Any]] = []
    trigger_map: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "recommended_workflow_mode": "tactical",
        "source_classes": [],
    })

    for category, items in categorized.items():
        for item in items:
            class_name = str(item.get("class") or "unknown")
            trigger = str(item.get("trigger") or "unknown")
            fix_pattern = str(item.get("fix_pattern") or "unknown")
            mode = str(item.get("recommended_workflow_mode") or "codex-assist")
            reason = str(item.get("reason") or "")
            heuristic = str(item.get("candidate_heuristic") or "")

            override = {
                "class": class_name,
                "category": category,
                "trigger": trigger,
                "fix_pattern": fix_pattern,
                "recommended_workflow_mode": mode,
                "reason": reason,
                "heuristic": heuristic,
                "stats": {
                    "total": item.get("total", 0),
                    "pass": item.get("pass", 0),
                    "partial": item.get("partial", 0),
                    "fail": item.get("fail", 0),
                },
            }
            class_overrides.append(override)

            cur = trigger_map[trigger]["recommended_workflow_mode"]
            trigger_map[trigger]["recommended_workflow_mode"] = _pick_more_conservative_mode(cur, mode)
            trigger_map[trigger]["source_classes"].append(class_name)

    decision_framework = plan.get("decision_framework", {})

    rules = {
        "version": "1",
        "generated_at_utc": generated_at,
        "source_plan_json": str(plan_path),
        "records_total": plan.get("records_total", 0),
        "default_workflow_mode": "tactical",
        "decision_framework": decision_framework,
        "mode_rank": MODE_RANK,
        "class_overrides": sorted(class_overrides, key=lambda x: x["class"]),
        "trigger_defaults": dict(sorted(trigger_map.items(), key=lambda kv: kv[0])),
        "operator_guidance": {
            "apply_cycle_limit": "Apply 1-2 local rule updates per cycle, then re-evaluate.",
            "fallback_rule": "If class/trigger is unknown, start tactical for routine work and escalate explicitly when blocked.",
        },
    }
    return rules


def main() -> int:
    args = parse_args()
    plan_path = Path(args.plan_json).resolve()
    out_file = Path(args.out_file).resolve()

    try:
        plan = load_plan(plan_path)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        return 1

    rules = build_rules(plan, plan_path)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote routing rules: {out_file}")
    print(f"Class overrides: {len(rules['class_overrides'])}")
    print(f"Trigger defaults: {len(rules['trigger_defaults'])}")

    if args.print:
        print(json.dumps(rules, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
