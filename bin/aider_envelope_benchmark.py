#!/usr/bin/env python3
"""Benchmark Aider envelope across a curated file-size range and task mix."""

from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import math
import os
import stat
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATE = dt.date.today().isoformat()
DEFAULT_TIMEOUT_SEC = int(os.environ.get("AIDER_ENVELOPE_TIMEOUT_SEC", "1200"))
DEFAULT_FILES = [
    "bin/aider_lib.py",
    "bin/aider_worker.py",
    "bin/aider_benchmark.py",
    "bin/stage5_manager.py",
    "bin/aider_guard.py",
    "bin/level10_qualify.py",
    "framework/worker_runtime.py",
    "domains/coding.py",
    "bin/codex51_learning_loop.py",
]

TASK_SPECS = {
    "docstring-add": {
        "description": "Add a one-line docstring to every function in this file that lacks one.",
        "tier": "Tier 1",
    },
    "bare-except-narrow": {
        "description": "Replace any bare 'except:' clauses with 'except Exception:'.",
        "tier": "Tier 1",
    },
    "type-hint-add": {
        "description": "Add type hints to all function signatures in this file.",
        "tier": "Tier 2",
    },
    "function-extract": {
        "description": "Extract any code block longer than 30 lines that appears inside a function into a separate helper function.",
        "tier": "Tier 2",
    },
}


def file_metrics(rel_path: str) -> dict[str, int]:
    path = REPO_ROOT / rel_path
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    function_count = sum(
        1
        for line in lines
        if line.lstrip().startswith("def ") or line.lstrip().startswith("class ")
    )
    return {
        "file_size_bytes": path.stat().st_size,
        "line_count": len(lines),
        "function_count": function_count,
    }


def estimate_prompt_tokens(prompt: str, rel_path: str) -> int:
    path = REPO_ROOT / rel_path
    text = path.read_text(encoding="utf-8", errors="replace")
    return max(1, math.ceil((len(prompt) + len(text)) / 4))


def read_text(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8", errors="replace")


def parse_tree(text: str) -> ast.AST | None:
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def iter_defs(tree: ast.AST | None):
    if tree is None:
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node


def count_missing_docstrings(tree: ast.AST | None) -> int:
    if tree is None:
        return 0
    count = 0
    for node in iter_defs(tree):
        if not ast.get_docstring(node):
            count += 1
    return count


def count_bare_excepts(tree: ast.AST | None) -> int:
    if tree is None:
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            count += 1
    return count


def count_unannotated_signatures(tree: ast.AST | None) -> int:
    if tree is None:
        return 0

    def _arg_missing(arg: ast.arg) -> bool:
        return arg.annotation is None

    count = 0
    for node in iter_defs(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        all_args = []
        all_args.extend(args.posonlyargs)
        all_args.extend(args.args)
        all_args.extend(args.kwonlyargs)
        if args.vararg is not None:
            all_args.append(args.vararg)
        if args.kwarg is not None:
            all_args.append(args.kwarg)
        if node.returns is None or any(_arg_missing(arg) for arg in all_args):
            count += 1
    return count


def max_function_span(tree: ast.AST | None) -> int:
    if tree is None:
        return 0
    spans = []
    for node in iter_defs(tree):
        lineno = getattr(node, "lineno", None)
        end_lineno = getattr(node, "end_lineno", None)
        if lineno is None or end_lineno is None:
            continue
        spans.append(max(0, int(end_lineno) - int(lineno) + 1))
    return max(spans) if spans else 0


def applicable_task(task_type: str, orig_text: str) -> bool:
    tree = parse_tree(orig_text)
    if task_type == "docstring-add":
        return count_missing_docstrings(tree) > 0
    if task_type == "bare-except-narrow":
        return count_bare_excepts(tree) > 0
    if task_type == "type-hint-add":
        return count_unannotated_signatures(tree) > 0
    if task_type == "function-extract":
        return max_function_span(tree) > 30
    raise KeyError(task_type)


def task_success(task_type: str, orig_text: str, new_text: str, exit_code: int, diff_bytes: int) -> tuple[bool, str]:
    orig_tree = parse_tree(orig_text)
    new_tree = parse_tree(new_text)
    orig_fn_count = sum(1 for _ in iter_defs(orig_tree))
    new_fn_count = sum(1 for _ in iter_defs(new_tree))

    if task_type == "docstring-add":
        orig_missing = count_missing_docstrings(orig_tree)
        new_missing = count_missing_docstrings(new_tree)
        if orig_missing == 0:
            return (exit_code == 0 and diff_bytes == 0, "no missing docstrings in original")
        if exit_code != 0:
            return (False, "wrapper exited non-zero")
        if diff_bytes == 0:
            return (False, "applicable task produced no diff")
        if orig_fn_count != new_fn_count:
            return (False, "function count changed")
        if new_missing != 0:
            return (False, f"{new_missing} defs still lack docstrings")
        return (True, "all missing docstrings added")

    if task_type == "bare-except-narrow":
        orig_bare = count_bare_excepts(orig_tree)
        new_bare = count_bare_excepts(new_tree)
        if orig_bare == 0:
            return (exit_code == 0 and diff_bytes == 0, "no bare excepts in original")
        if exit_code != 0:
            return (False, "wrapper exited non-zero")
        if diff_bytes == 0:
            return (False, "applicable task produced no diff")
        if orig_fn_count != new_fn_count:
            return (False, "function count changed")
        if new_bare != 0:
            return (False, f"{new_bare} bare excepts remain")
        return (True, "all bare excepts narrowed")

    if task_type == "type-hint-add":
        orig_unannot = count_unannotated_signatures(orig_tree)
        new_unannot = count_unannotated_signatures(new_tree)
        if orig_unannot == 0:
            return (exit_code == 0 and diff_bytes == 0, "all signatures already annotated")
        if exit_code != 0:
            return (False, "wrapper exited non-zero")
        if diff_bytes == 0:
            return (False, "applicable task produced no diff")
        if orig_fn_count != new_fn_count:
            return (False, "function count changed")
        if new_unannot != 0:
            return (False, f"{new_unannot} signatures still lack type hints")
        return (True, "all signatures annotated")

    if task_type == "function-extract":
        orig_span = max_function_span(orig_tree)
        new_span = max_function_span(new_tree)
        if orig_span <= 30:
            return (exit_code == 0 and diff_bytes == 0, "no function exceeds 30 lines in original")
        if exit_code != 0:
            return (False, "wrapper exited non-zero")
        if diff_bytes == 0:
            return (False, "applicable task produced no diff")
        if new_span >= orig_span:
            return (False, f"longest function span did not shrink ({orig_span} -> {new_span})")
        if new_fn_count < orig_fn_count:
            return (False, "function count decreased unexpectedly")
        return (True, f"longest function span shrank {orig_span} -> {new_span}")

    raise KeyError(task_type)


def run_command(cmd: list[str], cwd: Path, timeout_sec: int, env: dict[str, str] | None = None) -> tuple[int, str, float]:
    start = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        env=env,
    )
    duration = round(time.monotonic() - start, 2)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output, duration


def parse_verdict(output: str) -> str:
    for line in output.splitlines():
        if "verifier=AGREE" in line or "dual-loop=AGREE" in line:
            return "AGREE"
        if "verifier=DISAGREE" in line or "dual-loop=DISAGREE" in line:
            return "DISAGREE"
    return "N-A"


def layer1_passed(output: str) -> bool:
    if "PRE-FLIGHT BLOCK" in output:
        return False
    if "DIFF SANITY CHECK FAILED" in output:
        return False
    return True


def diff_size_bytes(rel_path: str) -> int:
    proc = subprocess.run(
        ["git", "diff", "--", rel_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return len((proc.stdout or "").encode("utf-8"))


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_type",
        "task_description",
        "file_path",
        "file_size_bytes",
        "line_count",
        "function_count",
        "prompt_token_estimate",
        "time_seconds",
        "exit_code",
        "diff_size_bytes",
        "layer1_pass",
        "layer1_5_verdict",
        "applicable",
        "success_boolean",
        "success_reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def summarize_cliff(rows: list[dict], key: str) -> tuple[str, float]:
    if not rows:
        return ("no data", 0.0)
    ordered = sorted(rows, key=lambda r: r[key])
    for idx in range(1, len(ordered) + 1):
        sample = ordered[:idx]
        success_rate = sum(1 for r in sample if r["success_boolean"]) / len(sample)
        if success_rate < 0.80:
            return (
                f"{ordered[idx - 1][key]} ({idx}/{len(sample)} cumulative success)",
                success_rate,
            )
    overall = sum(1 for r in ordered if r["success_boolean"]) / len(ordered)
    return ("no <80% cliff in sample", overall)


def task_bucket(rows: list[dict], task_type: str) -> list[dict]:
    return [row for row in rows if row["task_type"] == task_type]


def file_bucket(rows: list[dict], file_path: str) -> list[dict]:
    return [row for row in rows if row["file_path"] == file_path]


def write_report(rows: list[dict], path: Path, date_str: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Aider envelope benchmark (2D matrix)",
        "",
        f"- Date: {date_str}",
        f"- Sample size: {len(rows)} runs",
        "",
        "## Per-task success rate",
        "",
        "| task type | tier hint | success rate | cliff |",
        "|---|---|---:|---|",
    ]
    for task_type in TASK_SPECS:
        bucket = task_bucket(rows, task_type)
        if bucket:
            cliff, rate = summarize_cliff(bucket, "file_size_bytes")
            success_rate = sum(1 for r in bucket if r["success_boolean"]) / len(bucket)
        else:
            cliff, success_rate = ("no data", 0.0)
        lines.append(
            f"| `{task_type}` | {TASK_SPECS[task_type]['tier']} | {success_rate:.0%} | {cliff} |"
        )

    lines.extend([
        "",
        "## Per-file success rate across tasks",
        "",
        "| file | success rate | best/worst note |",
        "|---|---:|---|",
    ])
    for rel_path in DEFAULT_FILES:
        bucket = file_bucket(rows, rel_path)
        if bucket:
            success_rate = sum(1 for r in bucket if r["success_boolean"]) / len(bucket)
            notes = []
            for task_type in TASK_SPECS:
                for row in bucket:
                    if row["task_type"] == task_type and row["success_boolean"]:
                        notes.append(task_type)
                        break
            note = ", ".join(notes[:2]) if notes else "no successes"
            success_text = f"{success_rate:.0%}"
        else:
            success_text = "no data"
            note = "no runs"
        lines.append(f"| `{rel_path}` | {success_text} | {note} |")

    lines.extend([
        "",
        "## File-size cliff by task type",
        "",
        "| task type | cliff | success rate |",
        "|---|---|---:|",
    ])
    for task_type in TASK_SPECS:
        bucket = task_bucket(rows, task_type)
        cliff, rate = summarize_cliff(bucket, "file_size_bytes")
        rate_text = f"{rate:.0%}" if bucket else "no data"
        lines.append(f"| `{task_type}` | {cliff} | {rate_text} |")

    lines.extend([
        "",
        "## Routing recommendation",
        "",
    ])
    for task_type in TASK_SPECS:
        bucket = task_bucket(rows, task_type)
        if not bucket:
            recommendation = "no data"
        else:
            success_rate = sum(1 for r in bucket if r["success_boolean"]) / len(bucket)
            recommendation = "Tier 1" if task_type in ("docstring-add", "bare-except-narrow") and success_rate >= 0.80 else "Tier 2"
            if task_type in ("type-hint-add", "function-extract") and success_rate < 0.80:
                recommendation = "Tier 2"
        lines.append(f"- `{task_type}`: {recommendation}")

    lines.extend([
        "",
        "## Results",
        "",
        "| task | file | size bytes | lines | defs/classes | prompt tokens | seconds | exit | diff bytes | L1 | L1.5 | success |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| `{row['task_type']}` | `{row['file_path']}` | {row['file_size_bytes']} | {row['line_count']} "
            f"| {row['function_count']} | {row['prompt_token_estimate']} | {row['time_seconds']} | {row['exit_code']} "
            f"| {row['diff_size_bytes']} | {row['layer1_pass']} | {row['layer1_5_verdict']} | {row['success_boolean']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def task_types_to_run(value: str) -> list[str]:
    if value == "all":
        return list(TASK_SPECS)
    if value not in TASK_SPECS:
        raise argparse.ArgumentTypeError(f"unknown task type: {value}")
    return [value]


def run_one(task_type: str, rel_path: str, timeout_sec: int, date_str: str) -> dict:
    spec = TASK_SPECS[task_type]
    task_description = spec["description"]
    path = REPO_ROOT / rel_path
    original_bytes = path.read_bytes()
    original_mode = path.stat().st_mode
    original_text = original_bytes.decode("utf-8", errors="replace")
    metrics = file_metrics(rel_path)
    prompt_tokens = estimate_prompt_tokens(task_description, rel_path)

    env = os.environ.copy()
    env.setdefault(
        "AIDER_VERIFIER_PROMPT_TEMPLATE",
        str(REPO_ROOT / "config/prompts/library/v1.1.0/07-deepseek-verifier-prompt.md"),
    )

    cmd = [
        "bash",
        str(REPO_ROOT / "scripts" / "aider-task.sh"),
        "--quiet",
        "--class",
        "C0",
        task_description,
        rel_path,
    ]

    print(f"[aider-envelope] task={task_type} file={rel_path} size={metrics['file_size_bytes']} bytes")
    print(f"[aider-envelope] cmd={' '.join(cmd)}")

    exit_code = 1
    output = ""
    duration = 0.0
    layer1_verdict = "N-A"
    success = False
    success_reason = "not evaluated"
    try:
        exit_code, output, duration = run_command(cmd, REPO_ROOT, timeout_sec, env=env)
    except subprocess.TimeoutExpired as exc:
        duration = float(timeout_sec)
        output = (exc.stdout or "") + (exc.stderr or "")
        exit_code = 124
    finally:
        diff_bytes = diff_size_bytes(rel_path)
        if exit_code == 0 and diff_bytes > 0:
            layer1_verdict = parse_verdict(output)
        elif "verifier=" in output or "dual-loop=" in output:
            layer1_verdict = parse_verdict(output)
        if exit_code == 0:
            try:
                success, success_reason = task_success(
                    task_type, original_text, path.read_text(encoding="utf-8", errors="replace"), exit_code, diff_bytes
                )
            except Exception as exc:
                success = False
                success_reason = f"predicate-error: {exc}"
        else:
            success = False
            success_reason = f"wrapper exit {exit_code}"
        layer1_pass = int(layer1_passed(output))

        row = {
            "task_type": task_type,
            "task_description": task_description,
            "file_path": rel_path,
            **metrics,
            "prompt_token_estimate": prompt_tokens,
            "time_seconds": duration,
            "exit_code": exit_code,
            "diff_size_bytes": diff_bytes,
            "layer1_pass": layer1_pass,
            "layer1_5_verdict": layer1_verdict,
            "applicable": int(applicable_task(task_type, original_text)),
            "success_boolean": int(success),
            "success_reason": success_reason,
        }
        path.write_bytes(original_bytes)
        os.chmod(path, stat.S_IMODE(original_mode))

    print(
        f"[aider-envelope] exit={exit_code} duration={duration}s diff={row['diff_size_bytes']} "
        f"l1={row['layer1_pass']} l1.5={row['layer1_5_verdict']} success={row['success_boolean']}"
    )
    return row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark Aider envelope on a curated file list"
    )
    parser.add_argument(
        "--task-type",
        default="all",
        help="Task type to run: docstring-add, bare-except-narrow, type-hint-add, function-extract, or all",
    )
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    args = parser.parse_args()

    task_types = task_types_to_run(args.task_type)
    csv_path = REPO_ROOT / "artifacts" / f"aider_envelope_2d_{args.date}.csv"
    md_path = REPO_ROOT / "artifacts" / f"aider_envelope_2d_{args.date}.md"
    rows: list[dict] = []

    for task_type in task_types:
        for rel_path in args.files:
            rows.append(run_one(task_type, rel_path, args.timeout_sec, args.date))

    write_csv(rows, csv_path)
    write_report(rows, md_path, args.date)
    print(f"[aider-envelope] wrote {csv_path}")
    print(f"[aider-envelope] wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
