#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "aider_task_classes.json"
DEFAULT_TEMPLATE = BASE_DIR / "templates" / "aider-task-template.md"
TMP_DIR = BASE_DIR / "tmp"

if not CONFIG_PATH.exists():
    print(f"ERROR: missing config {CONFIG_PATH}", file=sys.stderr)
    sys.exit(1)

TASK_CLASSES = json.loads(CONFIG_PATH.read_text())


def slugify(value: str) -> str:
    safe = [c if c.isalnum() or c in {"_", "-", "."} else "-" for c in value]
    slug = "".join(safe).strip("-._")
    return slug or "task"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an automation-friendly Aider task brief"
    )
    parser.add_argument("--name", required=True, help="Task name")
    parser.add_argument("--class", dest="task_class", required=True,
                        choices=sorted(TASK_CLASSES.keys()))
    parser.add_argument("--objective", help="One-line objective")
    parser.add_argument("--goal", help="Alias for --objective")
    parser.add_argument("--file", action="append", dest="files",
                        help="Target file spec path[:action], repeatable")
    parser.add_argument("--out-file", dest="out_file", help="Optional output path")
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--out-of-scope", action="append", dest="oos", default=[])
    parser.add_argument("--acceptance", action="append", default=[])
    parser.add_argument("--validation", action="append", dest="extra_validations", default=[])
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--max-loc", type=int)
    parser.add_argument("--allow-extra", action="append", dest="allowed_extra", default=[])
    return parser.parse_args()


def parse_files(raw_files):
    if not raw_files:
        return []
    files = []
    for spec in raw_files:
        parts = spec.split(":", 1)
        path = parts[0].strip()
        if not path:
            continue
        action = parts[1].strip() if len(parts) == 2 else "modify"
        files.append({"path": path, "action": action})
    return files


def main():
    args = parse_args()
    task_class = args.task_class
    class_cfg = TASK_CLASSES[task_class]

    objective = args.objective or args.goal
    if not objective:
        print("ERROR: --objective/--goal is required", file=sys.stderr)
        sys.exit(1)

    files = parse_files(args.files)
    if not files:
        print("ERROR: at least one --file path[:action] is required", file=sys.stderr)
        sys.exit(1)

    limits = {
        "max_files": args.max_files or class_cfg["max_files"],
        "max_loc": args.max_loc or class_cfg["max_loc"],
        "allowed_extra_globs": sorted(set(class_cfg.get("allowed_extra_globs", [])) | set(args.allowed_extra))
    }

    constraints = class_cfg.get("default_constraints", []) + args.constraint
    out_of_scope = class_cfg.get("default_out_of_scope", []) + args.oos

    def dedupe(items):
        seen = []
        for item in items:
            if item and item not in seen:
                seen.append(item)
        return seen

    payload = {
        "task": {
            "name": args.name,
            "class": task_class,
            "generated_at": int(time.time())
        },
        "objective": objective,
        "target_files": files,
        "out_of_scope": dedupe(out_of_scope),
        "constraints": dedupe(constraints),
        "acceptance_criteria": args.acceptance or ["Validation commands must pass"],
        "validation_commands": args.extra_validations or class_cfg.get("validation_commands", []),
        "limits": limits,
        "escalate_if": class_cfg.get("escalate_if", [])
    }

    if not payload["validation_commands"]:
        print("ERROR: No validation commands defined for task", file=sys.stderr)
        sys.exit(1)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if args.out_file:
        out_path = Path(args.out_file)
        if not out_path.is_absolute():
            out_path = BASE_DIR / out_path
    else:
        slug = slugify(args.name)
        out_path = TMP_DIR / f"{slug}-{int(time.time())}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Created task brief: {out_path}")


if __name__ == "__main__":
    main()
