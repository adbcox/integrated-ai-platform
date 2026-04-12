#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from aider_lib import (
    describe_make_command,
    enforce_class_limits,
    ensure_paths_exist,
    forbid_patterns,
    load_task_classes,
    normalize_paths,
    parse_file_spec,
)

BASE_DIR = Path(__file__).resolve().parent.parent
START_TASK = BASE_DIR / "bin" / "aider_start_task.sh"
AIDER_LOOP = BASE_DIR / "bin" / "aider_loop.sh"

TASK_CLASSES = load_task_classes()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an automated Aider task with guardrails")
    parser.add_argument("--class", dest="task_class", required=True,
                        choices=sorted(TASK_CLASSES.keys()))
    parser.add_argument("--name", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--file", dest="files", action="append", required=True,
                        help="path[:action] to include in the brief")
    parser.add_argument("--task-file", dest="task_file")
    parser.add_argument("--workflow-mode", default=os.environ.get("WORKFLOW_MODE", "tactical"))
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--out-of-scope", dest="oos", action="append", default=[])
    parser.add_argument("--acceptance", action="append", default=[])
    parser.add_argument("--validation", dest="extra_validations", action="append", default=[])
    parser.add_argument("--allow-extra", dest="allowed_extra", action="append", default=[])
    parser.add_argument("--skip-guard", action="store_true")
    return parser.parse_args()


def run_cmd(cmd: list[str], env: dict | None = None):
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, env=env)


def main():
    args = parse_args()
    class_cfg = TASK_CLASSES[args.task_class]
    files = [parse_file_spec(spec) for spec in args.files]
    try:
        enforce_class_limits(files, class_cfg)
        ensure_paths_exist(files)
        forbidden = forbid_patterns(files, class_cfg.get("forbidden_globs", []))
        if forbidden:
            raise ValueError(
                "Targets hit forbidden globs: " + ", ".join(forbidden) + " (escalate to Codex)"
            )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: preflight failed -> {exc}", file=sys.stderr)
        print("Hint:", describe_make_command(args.task_class, args.name, args.objective, normalize_paths(files)))
        sys.exit(1)

    slug = "".join(c if c.isalnum() or c in {"-", "_", "."} else "-" for c in args.name)
    if not slug:
        slug = "task"
    if args.task_file:
        task_file = Path(args.task_file)
        if not task_file.is_absolute():
            task_file = BASE_DIR / task_file
    else:
        task_file = BASE_DIR / "tmp" / f"{slug}-{int(time.time())}.json"

    cmd = [str(START_TASK), "--name", args.name, "--class", args.task_class,
           "--objective", args.objective, "--out-file", str(task_file)]
    for spec in args.files:
        cmd += ["--file", spec]
    for item in args.constraint:
        cmd += ["--constraint", item]
    for item in args.oos:
        cmd += ["--out-of-scope", item]
    for item in args.acceptance:
        cmd += ["--acceptance", item]
    for item in args.extra_validations:
        cmd += ["--validation", item]
    for item in args.allowed_extra:
        cmd += ["--allow-extra", item]

    run_cmd(cmd)

    loop_cmd = [str(AIDER_LOOP), "--name", args.name, "--task-file", str(task_file), "--no-remote"]
    if args.skip_guard:
        loop_cmd.append("--skip-guard")
    env = os.environ.copy()
    env["WORKFLOW_MODE"] = args.workflow_mode
    run_cmd(loop_cmd, env=env)


if __name__ == "__main__":
    main()
