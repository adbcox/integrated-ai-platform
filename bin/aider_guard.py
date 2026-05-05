#!/usr/bin/env python3
# aider_guard.py — Layer 1 diff sanity check + scope guard (D-17-103)
#
# Two modes:
#   --task-file <json>   original task-JSON mode (batch pipeline)
#   --inline             operator mode: --description, --task-class, --files
#
# Exit codes:
#   0  all checks passed (or warn-only issues)
#   1  hard block (deletion rate exceeded, scope violation, no changes)
#   2  soft warn (truncation, suspicious shape) — aider-task.sh logs but continues
#
# Operator override: AIDER_SKIP_VALIDATOR=1 or --skip-validator
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Tuple
from fnmatch import fnmatch

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "aider_task_classes.json"
ARTIFACT_DIR = BASE_DIR / "artifacts" / "aider_runs"

TASK_CLASSES = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}


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


def diff_per_file_stats(files: List[str]) -> List[dict]:
    """Return per-file added/deleted line counts from git diff."""
    if not files:
        proc = subprocess.run(["git", "diff", "--numstat"], capture_output=True, text=True, check=True)
    else:
        proc = subprocess.run(["git", "diff", "--numstat", "--"] + files,
                               capture_output=True, text=True, check=True)
    results = []
    for line in proc.stdout.splitlines():
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        add, delete, path = parts[0], parts[1], parts[2]
        if add == "-" or delete == "-":
            continue  # binary — skip deletion check
        results.append({"path": path, "added": int(add), "deleted": int(delete)})
    return results


def original_line_count(path: str) -> int:
    """Count lines in file as it was before the current diff (HEAD version)."""
    try:
        proc = subprocess.run(["git", "show", f"HEAD:{path}"],
                               capture_output=True, text=True, check=True)
        return len(proc.stdout.splitlines())
    except subprocess.CalledProcessError:
        # File is new (untracked at HEAD) — no deletion check applies
        return 0


def is_append_task(description: str) -> bool:
    """Return True if task description signals an append/add operation."""
    desc_lower = description.lower()
    append_kws = ["append", "add ", "extend", "insert", "prepend", "attach"]
    return any(kw in desc_lower for kw in append_kws)


def has_disambiguator(description: str) -> bool:
    """Return True when the description carries structural disambiguation."""
    return bool(re.search(
        r"\b(line\s+\d+|function\s+\w+|method\s+\w+|inside\b|within\b|before\b|after\b|block\b)",
        description,
        re.IGNORECASE,
    ))


def detect_ambiguous_targets(description: str) -> list[str]:
    """Extract likely ambiguous target phrases from a task description."""
    desc = description.lower()
    targets: list[str] = []
    if "bare except" in desc or "except clause" in desc or "except clauses" in desc:
        targets.append("except")
    if "bare return" in desc or "return statement" in desc:
        targets.append("return")
    if "bare import" in desc or "import statement" in desc:
        targets.append("import")
    if "bare raise" in desc or "raise statement" in desc:
        targets.append("raise")
    if "bare continue" in desc:
        targets.append("continue")
    if "bare pass" in desc:
        targets.append("pass")
    return sorted(set(targets))


def _target_matches_for_file(path: str, target: str) -> tuple[int, int, list[int]]:
    """Return total match count, bare match count, and matching line numbers."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0, []

    total = 0
    bare = 0
    lines: list[int] = []

    if target == "except":
        pattern = re.compile(r"^\s*except\b")
        bare_pattern = re.compile(r"^\s*except\s*:\s*(#.*)?$")
    elif target == "return":
        pattern = re.compile(r"^\s*return\b")
        bare_pattern = pattern
    elif target == "import":
        pattern = re.compile(r"^\s*(?:import\b|from\b)")
        bare_pattern = pattern
    elif target == "raise":
        pattern = re.compile(r"^\s*raise\b")
        bare_pattern = pattern
    elif target == "continue":
        pattern = re.compile(r"^\s*continue\b")
        bare_pattern = pattern
    elif target == "pass":
        pattern = re.compile(r"^\s*pass\b")
        bare_pattern = pattern
    else:
        pattern = re.compile(rf"\b{re.escape(target)}\b")
        bare_pattern = pattern

    for idx, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            total += 1
            lines.append(idx)
        if bare_pattern.search(line):
            bare += 1
    return total, bare, lines


def pre_flight_target_check(
    description: str,
    file_path: str,
    allow_ambiguous: bool = False,
) -> List[Tuple[str, str]]:
    """Block ambiguous targets that need structural disambiguation."""
    if allow_ambiguous:
        return []
    if not file_path:
        return []

    issues: List[Tuple[str, str]] = []
    if has_disambiguator(description):
        return issues

    for target in detect_ambiguous_targets(description):
        total, bare, lines = _target_matches_for_file(file_path, target)
        if total <= 1:
            continue
        if target == "except" and bare == 1:
            issues.append((
                "block",
                f"ambiguous: {total} except clauses found, {bare} bare. "
                f"Specify by function name or unique pre/post context.",
            ))
        else:
            issues.append((
                "block",
                f"ambiguous target '{target}': {total} matches in {file_path} at lines {', '.join(map(str, lines[:6]))}. "
                f"Specify by function name or unique pre/post context.",
            ))
    return issues


def count_definitions(path: str) -> int:
    """Count function/class definitions in HEAD version of a file."""
    try:
        proc = subprocess.run(["git", "show", f"HEAD:{path}"],
                               capture_output=True, text=True, check=True)
        count = 0
        for line in proc.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                count += 1
        return count
    except subprocess.CalledProcessError:
        return 0


def check_insertion_expansion(
    changed_files: List[str],
    allow_large_insertions: bool = False,
) -> List[Tuple[str, str]]:
    """
    Block if insertions exceed 3× the function/class definition count in changed files.

    Catches duplication failures (Finding 23, D-17-109): a model that duplicates
    entire function bodies produces massive insertions relative to the file's
    definition density. A clean docstring/refactor adds lines proportional to scope.

    Threshold: total_insertions > 3 * total_definitions → BLOCK
    New files (no HEAD version) are excluded — they have no baseline definition count.
    """
    if allow_large_insertions:
        return []

    per_file = diff_per_file_stats(changed_files)
    # Only check Python files — definition counting is Python-specific
    py_files = [e for e in per_file if e["path"].endswith(".py")]
    if not py_files:
        return []

    total_insertions = sum(e["added"] for e in py_files)
    total_defs = sum(count_definitions(e["path"]) for e in py_files)

    if total_defs == 0:
        # All new files — no baseline, skip
        return []

    ratio = total_insertions / total_defs
    THRESHOLD = 3.0
    if ratio > THRESHOLD:
        return [(
            "block",
            f"insertion-expansion violation: {total_insertions} insertions "
            f"for {total_defs} definitions (ratio {ratio:.1f}x, threshold {THRESHOLD:.0f}x) — "
            f"possible duplication/hallucination. Use --allow-large-insertions to override.",
        )]
    return []


def check_deletion_rates(
    description: str,
    task_class: str,
    changed_files: List[str],
) -> List[Tuple[str, str]]:
    """
    Check per-file deletion rates.

    Returns list of (severity, message) tuples:
      "block" — hard failure
      "warn"  — soft warning
    """
    append_task = is_append_task(description)
    # Approved thresholds (D-17-103 operator decision):
    #   append tasks: 2% deletion is already suspicious
    #   general/refactor: 30%
    deletion_threshold = 0.02 if append_task else 0.30
    threshold_label = "2% (append task)" if append_task else "30%"

    issues = []
    per_file = diff_per_file_stats(changed_files)
    for entry in per_file:
        path = entry["path"]
        deleted = entry["deleted"]
        if deleted == 0:
            continue
        original = original_line_count(path)
        if original == 0:
            continue  # new file — no baseline
        rate = deleted / original
        if rate > deletion_threshold:
            issues.append((
                "block",
                f"{path}: deleted {deleted}/{original} lines "
                f"({rate:.0%} > threshold {threshold_label}) — "
                f"{'append task should delete nothing' if append_task else 'possible destructive rewrite'}",
            ))
    return issues


def check_truncation(
    description: str,
    changed_files: List[str],
) -> List[Tuple[str, str]]:
    """Warn if diff is suspiciously small relative to task complexity."""
    issues = []
    per_file = diff_per_file_stats(changed_files)
    multi_para_kws = ["append", "extend", "add section", "add §", "chronicle", "doctrine", "runbook"]
    desc_lower = description.lower()
    is_multi_para = len(description) > 150 or any(kw in desc_lower for kw in multi_para_kws)

    for entry in per_file:
        path = entry["path"]
        if not path.endswith(".md"):
            continue
        added = entry["added"]
        original = original_line_count(path)
        if original > 50 and is_multi_para and added <= 3:
            issues.append((
                "warn",
                f"{path}: only {added} lines added to a {original}-line doc for a "
                f"multi-paragraph task — possible Aider truncation",
            ))
    return issues


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


def run_inline_checks(
    description: str,
    task_class: str,
    files: List[str],
    allow_large_insertions: bool = False,
) -> int:
    """
    Inline guard mode — called from aider-task.sh after Aider runs.
    No task JSON file required.

    Returns:
      0  all clear
      1  hard block (operator must review before applying)
      2  soft warn (logged, but aider-task.sh continues)
    """
    print("[aider-guard] running inline diff sanity checks...")
    changed = [f for f in files if f]  # strip empties

    # If no explicit files passed, detect from git status
    if not changed:
        changed = git_changed_files()

    if not changed:
        print("[aider-guard] WARN: no changed files detected — nothing to check")
        return 0

    all_issues: List[Tuple[str, str]] = []
    for path in changed:
        all_issues.extend(pre_flight_target_check(description, path))
    all_issues.extend(check_deletion_rates(description, task_class, changed))
    all_issues.extend(check_truncation(description, changed))
    all_issues.extend(check_insertion_expansion(changed, allow_large_insertions))

    blocks = [(sev, msg) for sev, msg in all_issues if sev == "block"]
    warns  = [(sev, msg) for sev, msg in all_issues if sev == "warn"]

    for _, msg in warns:
        print(f"[aider-guard] WARN: {msg}", file=sys.stderr)

    if blocks:
        for _, msg in blocks:
            print(f"[aider-guard] BLOCK: {msg}", file=sys.stderr)
        print("[aider-guard] Diff sanity check FAILED — review diff before applying.")
        print("[aider-guard] Override: AIDER_SKIP_VALIDATOR=1 or --skip-validator")
        # Write artifact
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        artifact = ARTIFACT_DIR / f"guard-inline-{int(time.time())}.json"
        artifact.write_text(json.dumps({
            "mode": "inline",
            "description": description,
            "task_class": task_class,
            "files": changed,
            "blocks": [msg for _, msg in blocks],
            "warns": [msg for _, msg in warns],
            "timestamp": int(time.time()),
        }, indent=2) + "\n")
        print(f"[aider-guard] artifact: {artifact}")
        return 1

    if warns:
        print(f"[aider-guard] inline checks passed with {len(warns)} warning(s)")
        return 2

    print("[aider-guard] inline checks PASSED — diff looks clean")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Guardrail enforcement for Aider patches")
    parser.add_argument("--task-file", help="Task JSON file (batch pipeline mode)")
    parser.add_argument("--inline", action="store_true", help="Inline mode (from aider-task.sh)")
    parser.add_argument("--description", default="", help="Task description (inline / target-check mode)")
    parser.add_argument("--task-class", default="", help="Task class C0/C1/C2/C3 (inline mode)")
    parser.add_argument("--files", nargs="*", default=[], help="Changed files (inline mode)")
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--skip-validator", action="store_true",
                        help="Operator override: skip all guard checks")
    parser.add_argument("--allow-large-insertions", action="store_true",
                        help="Bypass insertion-expansion check for legitimate large refactors")
    parser.add_argument("--target-check", action="store_true",
                        help="Run only the ambiguous-target pre-flight check")
    parser.add_argument("--file-path", default="", help="Single file path (target-check mode)")
    parser.add_argument("--allow-ambiguous", action="store_true",
                        help="Bypass the ambiguous-target pre-flight check")
    args = parser.parse_args()

    # Operator override via flag or env
    import os
    if args.skip_validator or os.environ.get("AIDER_SKIP_VALIDATOR") == "1":
        print("[aider-guard] SKIPPED (operator override)")
        sys.exit(0)

    if args.target_check:
        issues = pre_flight_target_check(
            args.description,
            args.file_path,
            allow_ambiguous=args.allow_ambiguous,
        )
        if issues:
            for sev, msg in issues:
                print(f"[aider-guard] {sev.upper()}: {msg}", file=sys.stderr)
            artifact = ARTIFACT_DIR / f"guard-target-{int(time.time())}.json"
            ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
            artifact.write_text(json.dumps({
                "mode": "target_check",
                "description": args.description,
                "file_path": args.file_path,
                "blocks": [msg for sev, msg in issues if sev == "block"],
                "warns": [msg for sev, msg in issues if sev == "warn"],
                "timestamp": int(time.time()),
            }, indent=2) + "\n")
            print(f"[aider-guard] artifact: {artifact}", file=sys.stderr)
            sys.exit(1)
        print("[aider-guard] target-check PASSED")
        sys.exit(0)

    # Inline mode — wired from aider-task.sh
    if args.inline:
        rc = run_inline_checks(
            args.description, args.task_class, args.files,
            allow_large_insertions=args.allow_large_insertions,
        )
        sys.exit(rc)

    # Original task-file mode
    if not args.task_file:
        print("ERROR: --task-file or --inline required", file=sys.stderr)
        sys.exit(1)

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
