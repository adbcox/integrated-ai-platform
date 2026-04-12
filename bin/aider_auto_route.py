#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from aider_lib import (
    classify_roots,
    fnmatch_any,
    load_task_classes,
    parse_file_spec,
)

BASE_DIR = Path(__file__).resolve().parent.parent
RUNNER = BASE_DIR / "bin" / "aider_task_runner.py"

TASK_CLASSES = load_task_classes()


def parse_args():
    parser = argparse.ArgumentParser(description="Auto-classify a task and run the Aider pipeline")
    parser.add_argument("--name", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--file", action="append", dest="files", required=True,
                        help="path[:action] entry; repeatable")
    parser.add_argument("--force-class", choices=sorted(TASK_CLASSES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workflow-mode", default=os.environ.get("WORKFLOW_MODE", "tactical"))
    return parser.parse_args()


def is_docs(paths: list[str]) -> bool:
    lowered = [p.lower() for p in paths]
    return all(p.startswith("docs/") or p.endswith(".md") or p.endswith(".rst") or p == "readme.md" for p in lowered)


def is_tests(paths: list[str]) -> bool:
    lowered = [p.lower() for p in paths]
    return all("tests/" in p or p.endswith("_test.sh") or p.endswith("_test.py") for p in lowered)


def guess_class(objective: str, files):
    paths = [spec.path for spec in files]
    objective_l = objective.lower()
    if is_docs(paths):
        return "docs-sync"
    if is_tests(paths) or "test" in objective_l:
        return "test-repair"
    if any(keyword in objective_l for keyword in ("lint", "format", "style", "typo")):
        return "lint-fix"
    if any(keyword in objective_l for keyword in ("typing", "annotation", "type hint")):
        return "typed-cleanup"
    if "refactor" in objective_l:
        return "refactor-narrow"
    if any(keyword in objective_l for keyword in ("feature", "flag", "toggle")):
        return "targeted-feature-patch"
    roots = classify_roots(files)
    if roots["count"] > 1:
        return "refactor-narrow"
    return "bugfix-small"


def ensure_limits(task_class: str, files):
    cfg = TASK_CLASSES[task_class]
    if len(files) > cfg.get("max_files", 3):
        raise ValueError(
            f"Requested files ({len(files)}) exceed limit for {task_class} ({cfg['max_files']}); split or escalate"
        )
    roots = classify_roots(files)
    max_roots = cfg.get("max_roots")
    if max_roots and roots["count"] > max_roots:
        raise ValueError(
            f"Files span {roots['count']} roots ({', '.join(roots['roots'])}) which exceeds limit ({max_roots})"
        )
    forbidden = cfg.get("forbidden_globs", [])
    if forbidden and fnmatch_any((spec.path for spec in files), forbidden):
        raise ValueError("Files include forbidden paths; escalate to Codex")


def build_runner_cmd(args, task_class):
    cmd = [str(RUNNER), "--class", task_class, "--name", args.name,
           "--objective", args.objective, "--workflow-mode", args.workflow_mode]
    for spec in args.files:
        cmd += ["--file", spec]
    return cmd


def main():
    args = parse_args()
    files = [parse_file_spec(spec) for spec in args.files]
    task_class = args.force_class or guess_class(args.objective, files)
    try:
        ensure_limits(task_class, files)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"aider-auto classified '{args.name}' as {task_class}")
        sys.exit(0)

    cmd = build_runner_cmd(args, task_class)
    print(f"[aider-auto] routing to class {task_class}")
    os.execv(cmd[0], cmd)


if __name__ == "__main__":
    main()
