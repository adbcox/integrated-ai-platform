#!/usr/bin/env python3
"""Resolve recommended WORKFLOW_MODE from local routing rules."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_rules = Path(os.environ.get("RULES_FILE", str(base_dir / "policies" / "local-routing-rules.json")))

    parser = argparse.ArgumentParser(description="Select workflow mode using local routing rules.")
    parser.add_argument("--class", dest="class_name", default="", help="Class key: '<trigger> | <fix_pattern>'")
    parser.add_argument("--trigger", default="", help="Escalation trigger")
    parser.add_argument("--fix-pattern", default="", help="Fix/root-cause pattern")
    parser.add_argument("--rules-file", default=str(default_rules), help="Routing rules file")
    parser.add_argument("--shell-export", action="store_true", help="Print export WORKFLOW_MODE=<mode>")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def load_rules(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Rules file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_class_key(args: argparse.Namespace) -> str:
    if args.class_name:
        return args.class_name.strip()
    if args.trigger and args.fix_pattern:
        return f"{args.trigger.strip()} | {args.fix_pattern.strip()}"
    return ""


def select_mode(rules: dict[str, Any], class_key: str, trigger: str) -> dict[str, str]:
    default_mode = str(rules.get("default_workflow_mode") or "tactical")

    for item in rules.get("class_overrides", []):
        if str(item.get("class")) == class_key and class_key:
            return {
                "mode": str(item.get("recommended_workflow_mode") or default_mode),
                "source": "class_override",
                "reason": str(item.get("reason") or "matched class override"),
                "class": class_key,
            }

    trigger_defaults = rules.get("trigger_defaults", {})
    if trigger and trigger in trigger_defaults:
        td = trigger_defaults[trigger]
        return {
            "mode": str(td.get("recommended_workflow_mode") or default_mode),
            "source": "trigger_default",
            "reason": f"matched trigger default: {trigger}",
            "class": class_key,
        }

    return {
        "mode": default_mode,
        "source": "global_default",
        "reason": "no specific class or trigger rule matched",
        "class": class_key,
    }


def main() -> int:
    args = parse_args()
    rules_path = Path(args.rules_file).resolve()

    try:
        rules = load_rules(rules_path)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        return 1

    class_key = resolve_class_key(args)
    trigger = args.trigger.strip()
    result = select_mode(rules, class_key, trigger)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    if args.shell_export:
        print(f"export WORKFLOW_MODE={result['mode']}")
        return 0

    print(f"WORKFLOW_MODE={result['mode']}")
    print(f"source: {result['source']}")
    print(f"reason: {result['reason']}")
    if result["class"]:
        print(f"class: {result['class']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
