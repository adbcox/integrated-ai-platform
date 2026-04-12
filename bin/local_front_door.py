#!/usr/bin/env python3
"""Single-command local front door that links intake to the aider loop."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


def shlex_join(cmd: Sequence[str]) -> str:
    try:
        return shlex.join(cmd)
    except AttributeError:  # Python <3.8 fallback
        return " ".join(shlex.quote(token) for token in cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local-first entrypoint that runs intake and launches the aider loop",
    )
    parser.add_argument("--name", required=True, help="Task name")
    parser.add_argument("--goal", required=True, help="Task goal or objective")
    parser.add_argument("--class", dest="class_name", default="", help="Class '<trigger> | <fix_pattern>'")
    parser.add_argument("--trigger", default="", help="Escalation trigger name")
    parser.add_argument("--fix-pattern", default="", help="Fix/root-cause pattern")
    parser.add_argument("--constraint", dest="constraints", action="append", default=[], help="Constraint text (repeatable)")
    parser.add_argument("--escalate", choices=["auto", "yes", "no"], default="auto", help="Escalation packet policy")
    parser.add_argument("--task-id", default="", help="Explicit task id (optional)")
    parser.add_argument("--intake-only", action="store_true", help="Run intake but skip the aider loop")
    parser.add_argument("--dry-run", action="store_true", help="Show the derived commands without executing them")
    parser.add_argument(
        "--loop-arg",
        action="append",
        default=[],
        help="Extra argument forwarded to aider_loop (repeat to add more tokens)",
    )
    return parser.parse_args()


def build_intake_cmd(bin_dir: Path, args: argparse.Namespace) -> list[str]:
    cmd = [sys.executable, str(bin_dir / "local_task_intake.py"), "--name", args.name, "--goal", args.goal, "--json"]
    if args.class_name:
        cmd += ["--class", args.class_name]
    if args.trigger:
        cmd += ["--trigger", args.trigger]
    if args.fix_pattern:
        cmd += ["--fix-pattern", args.fix_pattern]
    if args.task_id:
        cmd += ["--task-id", args.task_id]
    if args.constraints:
        for item in args.constraints:
            cmd += ["--constraints", item]
    if args.escalate:
        cmd += ["--escalate", args.escalate]
    return cmd


def run_subprocess(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, env=env)


def ensure_success(proc: subprocess.CompletedProcess[str], label: str) -> None:
    if proc.returncode == 0:
        return
    sys.stderr.write(f"ERROR: {label} failed (exit {proc.returncode})\n")
    if proc.stdout:
        sys.stderr.write(proc.stdout + "\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr + "\n")
    raise SystemExit(proc.returncode)


def parse_intake_output(stdout: str) -> dict[str, Any]:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        sys.stderr.write("ERROR: could not parse intake JSON output\n")
        sys.stderr.write(f"reason: {exc}\n")
        sys.stderr.write(stdout + "\n")
        raise SystemExit(1)


def main() -> int:
    args = parse_args()
    bin_dir = Path(__file__).resolve().parent
    repo_dir = bin_dir.parent

    intake_cmd = build_intake_cmd(bin_dir, args)
    print(f"[front-door] intake command: {shlex_join(intake_cmd)}")
    intake_proc = run_subprocess(intake_cmd)
    ensure_success(intake_proc, "local_task_intake")
    intake = parse_intake_output(intake_proc.stdout)

    recommended = str(intake.get("recommended_workflow_mode") or "codex-assist")
    routing_source = intake.get("routing_source", "unknown")
    routing_reason = intake.get("routing_reason", "")
    task_id = intake.get("task_id", "unknown")
    heuristic = intake.get("applied_heuristic") or ""
    intake_dir = Path(intake.get("intake_dir", repo_dir / "artifacts" / "intake"))

    print(f"[front-door] task_id: {task_id}")
    print(f"[front-door] recommended mode: {recommended} ({routing_source}: {routing_reason})")
    if heuristic:
        print(f"[front-door] applied heuristic: {heuristic}")
    print(f"[front-door] intake artifacts: {intake_dir}")
    if bool(intake.get("packet_written")):
        print(f"[front-door] escalation packet: {intake_dir / 'codex-escalation-packet.md'}")

    if args.intake_only:
        return 0

    loop_cmd = [str(bin_dir / "aider_loop.sh"), "--workflow-mode", recommended, "--name", args.name]
    if args.goal:
        loop_cmd += ["--goal", args.goal]
    for extra in args.loop_arg:
        loop_cmd.append(extra)

    env = os.environ.copy()
    env.setdefault("WORKFLOW_MODE", recommended)
    if task_id:
        env.setdefault("TASK_ID", task_id)
    env.setdefault("INTAKE_DIR", str(intake_dir))

    print(f"[front-door] aider loop command: {shlex_join(loop_cmd)}")
    if args.dry_run:
        return 0

    loop_proc = subprocess.run(loop_cmd, env=env)
    return loop_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
