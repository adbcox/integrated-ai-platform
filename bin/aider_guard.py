#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from fnmatch import fnmatch

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "aider_task_classes.json"
ARTIFACT_DIR = BASE_DIR / "artifacts" / "aider_runs"

if not CONFIG_PATH.exists():
    print(f"ERROR: missing config {CONFIG_PATH}", file=sys.stderr)
    sys.exit(1)

TASK_CLASSES = json.loads(CONFIG_PATH.read_text())


def load_task(task_file: Path) -> dict:
    data = json.loads(task_file.read_text())
    if "task" not in data or "class" not in data["task"]:
        raise ValueError("task file missing task.class")
    return data


def git_changed_files() -> list:
    proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    files = []
    for line in proc.stdout.splitlines():
        # Keep leading spaces: porcelain v1 encodes unstaged changes as " M path".
        line = line.rstrip()
        if not line:
            continue
        status, path = line[:2], line[3:]
        path = path.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[-1]
        if path.startswith("artifacts/aider_runs"):
            continue
        files.append(path)
    return sorted(set(files))


def diff_size() -> int:
    proc = subprocess.run(["git", "diff", "--numstat"], capture_output=True, text=True, check=True)
    total = 0
    for line in proc.stdout.splitlines():
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        add, delete = parts[0], parts[1]
        if add == "-" or delete == "-":
            raise ValueError("Binary diff detected; escalate to Codex")
        total += int(add) + int(delete)
    return total


def validate_scope(task: dict, changed_files: list, class_cfg: dict):
    allowed = {entry["path"] for entry in task.get("target_files", [])}
    extra_globs = set(task.get("limits", {}).get("allowed_extra_globs", []))
    extra_globs.update(class_cfg.get("allowed_extra_globs", []))
    forbidden_globs = set(class_cfg.get("forbidden_globs", []))
    violations = []
    for path in changed_files:
        if forbidden_globs and any(fnmatch(path, glob) for glob in forbidden_globs):
            raise ValueError(f"Changed file '{path}' matches forbidden glob; escalate to Codex")
        if path in allowed:
            continue
        matched = any(fnmatch(path, pattern) for pattern in extra_globs)
        if not matched:
            violations.append(path)
    if violations:
        raise ValueError(f"Changed files outside approved scope: {', '.join(violations)}")


class GuardError(Exception):
    def __init__(self, code: str, message: str, *, results=None, context=None):
        super().__init__(message)
        self.code = code
        self.results = results or []
        self.context = context or {}


def run_validations(commands):
    results = []
    for cmd in commands:
        print(f"[aider-guard] running validation: {cmd}")
        start = time.time()
        try:
            subprocess.run(cmd, shell=True, check=True)
            results.append({
                "command": cmd,
                "status": "passed",
                "duration_sec": round(time.time() - start, 2)
            })
        except subprocess.CalledProcessError as exc:
            results.append({
                "command": cmd,
                "status": "failed",
                "duration_sec": round(time.time() - start, 2),
                "returncode": exc.returncode
            })
            raise GuardError("validation_failed", f"Validation '{cmd}' failed (exit {exc.returncode})", results=results) from exc
    return results


def write_artifact(task, status, *, changed_files=None, diff_lines=None,
                   validations=None, failure_code=None, reason=None, suggested_action=None,
                   context=None):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    slug = task["task"].get("name", task["task"].get("class", "task"))
    slug = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in slug)
    artifact = ARTIFACT_DIR / f"{slug}-{int(time.time())}.json"
    payload = {
        "task_file": task.get("_source_file"),
        "task_class": task["task"].get("class"),
        "objective": task.get("objective", ""),
        "status": status,
        "failure_code": failure_code,
        "reason": reason,
        "suggested_action": suggested_action,
        "changed_files": changed_files or [],
        "diff_lines": diff_lines,
        "validation_commands": task.get("validation_commands"),
        "validations": validations or [],
        "timestamp": int(time.time())
    }
    if context:
        payload["context"] = context
    artifact.write_text(json.dumps(payload, indent=2) + "\n")
    return artifact


def hint_for(code: str) -> Optional[str]:
    return {
        "scope_violation": "Tighten file list or split the task",
        "diff_budget": "Break the change into smaller patches",
        "validation_failed": "Inspect failing validation output and fix root cause",
        "no_changes": "Ensure the patch was applied before running guard",
        "unknown": "Escalate to Codex for review"
    }.get(code, None)


def main():
    parser = argparse.ArgumentParser(description="Guardrail enforcement for Aider patches")
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()

    task_path = Path(args.task_file)
    if not task_path.exists():
        print(f"ERROR: missing task file {task_path}", file=sys.stderr)
        sys.exit(1)

    task = load_task(task_path)
    task["_source_file"] = str(task_path)
    class_name = task["task"]["class"]
    class_cfg = TASK_CLASSES.get(class_name)
    if not class_cfg:
        print(f"ERROR: unknown task class {class_name}", file=sys.stderr)
        sys.exit(1)

    changed = []
    size = None
    validation_results = []

    try:
        changed = git_changed_files()
        if not changed:
            raise GuardError("no_changes", "No changes detected; apply patch before running guard")

        limits = task.get("limits", {})
        max_files = limits.get("max_files", class_cfg.get("max_files", 3))
        max_loc = limits.get("max_loc", class_cfg.get("max_loc", 200))
        max_roots = limits.get("max_roots", class_cfg.get("max_roots"))

        if len(changed) > max_files:
            raise GuardError(
                "scope_violation",
                f"Changed files ({len(changed)}) exceed limit ({max_files})",
                context={"changed_files": changed, "limit": max_files},
            )

        try:
            validate_scope(task, changed, class_cfg)
        except ValueError as scope_exc:
            raise GuardError(
                "scope_violation",
                str(scope_exc),
                context={"changed_files": changed},
            ) from scope_exc

        if max_roots:
            roots = sorted({path.split("/", 1)[0] for path in changed})
            if len(roots) > max_roots:
                raise GuardError(
                    "scope_violation",
                    f"Changed directories ({len(roots)}) exceed limit ({max_roots})",
                    context={"roots": roots, "limit": max_roots},
                )

        size = diff_size()
        if size > max_loc:
            raise GuardError(
                "diff_budget",
                f"Diff size {size} lines exceeds limit {max_loc}",
                context={"diff_lines": size, "limit": max_loc},
            )

        validation_commands = task.get("validation_commands", class_cfg.get("validation_commands", []))
        if not validation_commands and not args.skip_validation:
            raise GuardError("validation_missing", "No validation commands configured for this task")

        if not args.skip_validation and validation_commands:
            validation_results = run_validations(validation_commands)

        artifact = write_artifact(
            task,
            "passed",
            changed_files=changed,
            diff_lines=size,
            validations=validation_results,
            failure_code=None,
            reason=None,
            suggested_action=None,
            context={
                "workflow_mode": task.get("workflow_mode"),
            },
        )
        print(f"[aider-guard] scope + validation checks PASSED ({artifact})")
    except GuardError as exc:
        context = exc.context or {}
        if exc.code in {"scope_violation", "diff_budget"}:
            context.setdefault("changed_files", changed)
            if size is not None:
                context.setdefault("diff_lines", size)
        artifact = write_artifact(
            task,
            "failed",
            changed_files=changed,
            diff_lines=size,
            validations=exc.results if exc.results else validation_results,
            failure_code=exc.code,
            reason=str(exc),
            suggested_action=hint_for(exc.code),
            context=context,
        )
        print(f"[aider-guard] FAILURE ({exc.code}): {exc}. See {artifact}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
