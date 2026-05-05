#!/usr/bin/env python3
"""Benchmark Aider envelope across a curated file-size range."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import os
import stat
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATE = dt.date.today().isoformat()
DEFAULT_PROMPT = "Add type hints to all function signatures."
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


def file_metrics(rel_path: str) -> dict[str, int]:
    path = REPO_ROOT / rel_path
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    function_count = sum(
        1 for line in lines
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


def run_command(cmd: list[str], cwd: Path, timeout_sec: int) -> tuple[int, str, float]:
    start = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
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


def guard_passed(output: str, exit_code: int) -> bool:
    if "DIFF SANITY CHECK FAILED" in output or "PRE-FLIGHT BLOCK" in output:
        return False
    return exit_code == 0 and "Aider modified" in output


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
        "file_path",
        "file_size_bytes",
        "line_count",
        "function_count",
        "prompt_token_estimate",
        "time_to_complete_sec",
        "exit_code",
        "diff_size_bytes",
        "layer1_pass",
        "layer1_5_verdict",
        "success",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def summarize_cliff(rows: list[dict], key: str) -> tuple[str, float]:
    ordered = sorted(rows, key=lambda r: r[key])
    for idx in range(1, len(ordered) + 1):
        sample = ordered[:idx]
        success_rate = sum(1 for r in sample if r["success"]) / len(sample)
        if success_rate < 0.80:
            return f"{ordered[idx - 1][key]} ({idx}/{len(sample)} cumulative success)", success_rate
    return "no <80% cliff in sample", sum(1 for r in ordered if r["success"]) / len(ordered)


def write_report(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    size_cliff, size_rate = summarize_cliff(rows, "file_size_bytes")
    fn_cliff, fn_rate = summarize_cliff(rows, "function_count")

    lines = [
        "# Aider envelope benchmark",
        "",
        f"- Date: {DEFAULT_DATE}",
        f"- Prompt: `{DEFAULT_PROMPT}`",
        f"- Sample size: {len(rows)} files",
        "",
        "## Cliff summary",
        f"- Size cliff: {size_cliff} (success rate {size_rate:.0%})",
        f"- Function-count cliff: {fn_cliff} (success rate {fn_rate:.0%})",
        "",
        "## Results",
        "",
        "| file | size bytes | lines | defs/classes | prompt tokens | seconds | exit | diff bytes | L1 | L1.5 | success |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['file_path']}` | {row['file_size_bytes']} | {row['line_count']} | {row['function_count']} "
            f"| {row['prompt_token_estimate']} | {row['time_to_complete_sec']} | {row['exit_code']} "
            f"| {row['diff_size_bytes']} | {row['layer1_pass']} | {row['layer1_5_verdict']} | {row['success']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Aider envelope on a curated file list")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    args = parser.parse_args()

    csv_path = REPO_ROOT / "artifacts" / f"aider_envelope_{args.date}.csv"
    md_path = REPO_ROOT / "artifacts" / f"aider_envelope_{args.date}.md"
    rows: list[dict] = []

    for rel_path in args.files:
        path = REPO_ROOT / rel_path
        original_bytes = path.read_bytes()
        original_mode = path.stat().st_mode
        metrics = file_metrics(rel_path)
        prompt_tokens = estimate_prompt_tokens(args.prompt, rel_path)
        cmd = [
            "bash",
            str(REPO_ROOT / "bin" / "aider_local.sh"),
            "--no-detect-urls",
            "--map-tokens",
            "0",
            "--message",
            args.prompt,
            rel_path,
        ]
        print(f"[aider-envelope] file={rel_path} size={metrics['file_size_bytes']} bytes")
        print(f"[aider-envelope] cmd={' '.join(cmd)}")

        exit_code = 1
        output = ""
        duration = 0.0
        guard_output = ""
        guard_exit = 1
        verifier_output = ""
        verifier_exit = 3
        try:
            exit_code, output, duration = run_command(cmd, REPO_ROOT, args.timeout_sec)
        except subprocess.TimeoutExpired as exc:
            duration = float(args.timeout_sec)
            output = (exc.stdout or "") + (exc.stderr or "")
            exit_code = 124
        finally:
            diff_bytes = diff_size_bytes(rel_path)
            if exit_code == 0 and diff_bytes > 0:
                guard_cmd = [
                    "python3",
                    str(REPO_ROOT / "bin" / "aider_guard.py"),
                    "--inline",
                    "--description",
                    args.prompt,
                    "--task-class",
                    "C0",
                    "--files",
                    rel_path,
                ]
                try:
                    guard_exit, guard_output, _ = run_command(guard_cmd, REPO_ROOT, 300)
                except subprocess.TimeoutExpired:
                    guard_exit = 1
                    guard_output = "[aider-envelope] guard timeout"
                if guard_exit in (0, 2):
                    verifier_cmd = [
                        "python3",
                        str(REPO_ROOT / "bin" / "aider_verifier.py"),
                        "--description",
                        args.prompt,
                        "--file-path",
                        rel_path,
                        "--diff-stdin",
                        "--quiet",
                    ]
                    try:
                        verifier_exit, verifier_output, _ = run_command(
                            verifier_cmd, REPO_ROOT, 300
                        )
                    except subprocess.TimeoutExpired:
                        verifier_exit = 3
                        verifier_output = "[aider-envelope] verifier timeout"
                else:
                    verifier_output = guard_output
                    verifier_exit = guard_exit
            layer1_pass = int(guard_exit in (0, 2))
            layer1_5 = parse_verdict(verifier_output) if verifier_output else "N-A"
            success = bool(exit_code == 0 and diff_bytes > 0 and layer1_pass and layer1_5 != "DISAGREE")
            rows.append({
                "file_path": rel_path,
                **metrics,
                "prompt_token_estimate": prompt_tokens,
                "time_to_complete_sec": duration,
                "exit_code": exit_code,
                "diff_size_bytes": diff_bytes,
                "layer1_pass": layer1_pass,
                "layer1_5_verdict": layer1_5,
                "success": int(success),
            })
            path.write_bytes(original_bytes)
            os.chmod(path, stat.S_IMODE(original_mode))

        print(
            f"[aider-envelope] exit={exit_code} duration={duration}s diff={rows[-1]['diff_size_bytes']} "
            f"l1={rows[-1]['layer1_pass']} l1.5={rows[-1]['layer1_5_verdict']} success={rows[-1]['success']}"
        )

    write_csv(rows, csv_path)
    write_report(rows, md_path)
    print(f"[aider-envelope] wrote {csv_path}")
    print(f"[aider-envelope] wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
