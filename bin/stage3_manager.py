#!/usr/bin/env python3
"""Manager-1 orchestrator for Stage-3 literal/comment worker jobs."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_RAG = REPO_ROOT / "bin" / "stage_rag1_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "stage3_manager"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
EVENT_LOG = REPO_ROOT / "artifacts" / "micro_runs" / "events.jsonl"


FAILURE_CLASS_MAP = {
    "literal_replace_missing_old": "literal_replace_missing_old",
    "literal_replace_fallback": "clean_literal_replace_failure",
    "literal_shell_risky": "literal_shell_risky",
    "prompt_contract_rejection": "prompt_contract_rejection",
    "missing_file_ref": "missing_file_ref",
    "missing_anchor": "missing_anchor",
    "no_change": "clean_no_op_rejection",
    "comment_scope": "clean_comment_scope_rejection",
    "repo_unwritable": "external_repo_writability_block",
    "fallback_blocked_running_script": "fallback_blocked_running_script",
}

FALLBACK_TAGS = {"literal_fallback_start", "literal_fallback_applied"}


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("check", True)
    return subprocess.run(cmd, **kwargs)


def git_clean() -> None:
    result = run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    if result.stdout.strip():
        raise SystemExit("Working tree must be clean before running manager")


def stage_rag(query: str, plan_id: str, target: str, lines: str, notes: str, top: int) -> None:
    if not STAGE_RAG.exists():
        raise SystemExit(f"Missing Stage RAG helper: {STAGE_RAG}")
    tokens = shlex.split(query)
    if not tokens:
        raise SystemExit("Query must produce at least one token")
    cmd = [
        sys.executable,
        str(STAGE_RAG),
        "--stage",
        "stage3",
        "--plan-id",
        plan_id,
        "--top",
        str(top),
        "--selected-path",
        target,
        "--selected-lines",
        lines,
    ]
    if notes:
        cmd.extend(["--notes", notes])
    cmd.append("--")
    cmd.extend(tokens)
    run(cmd)


def write_message_file(job_id: str, message: str) -> Path:
    path = Path(tempfile.gettempdir()) / f"stage3_job_{job_id}.msg"
    path.write_text(message.strip() + "\n", encoding="utf-8")
    return path


def run_worker(message_file: Path, target: str, plan_id: str) -> int:
    env = os.environ.copy()
    env["AIDER_MICRO_STAGE"] = "stage3"
    env["AIDER_MICRO_PLAN_ID"] = plan_id
    cmd = [
        "make",
        "aider-micro-safe",
        f"AIDER_MICRO_MESSAGE_FILE={message_file}",
        f"AIDER_MICRO_FILES={target}",
    ]
    proc = subprocess.run(cmd, env=env)
    return proc.returncode


def load_events(plan_id: str) -> list[dict]:
    if not EVENT_LOG.exists():
        return []
    events: list[dict] = []
    with EVENT_LOG.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("plan_id") == plan_id:
                events.append(record)
    return events


def classify(events: list[dict]) -> tuple[str, bool, bool, str | None]:
    fallback_used = any(evt.get("tag") in FALLBACK_TAGS for evt in events)
    accepted = False
    classification = "unknown"
    final_tag = None
    final = None
    for evt in reversed(events):
        if evt.get("status") in {"success", "failure"}:
            final = evt
            break
    if final:
        status = final.get("status")
        tag = final.get("tag") or "completed"
        final_tag = tag
        if status == "success":
            accepted = True
            classification = "aider_exit_recovered" if fallback_used else "accepted_change"
        else:
            classification = FAILURE_CLASS_MAP.get(tag, tag)
    return classification, fallback_used, accepted, final_tag


def commit_changes(target: str, commit_msg: str) -> str | None:
    status = run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    if not status.stdout.strip():
        return None
    run(["git", "add", target])
    run(["git", "commit", "-m", commit_msg])
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return head.stdout.strip()


def append_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage-3 manager orchestrator")
    parser.add_argument("--query", required=True, help="Stage RAG planning query")
    parser.add_argument("--target", required=True, help="Target file for the worker")
    parser.add_argument("--message", required=True, help="Literal/comment instruction for the worker")
    parser.add_argument("--commit-msg", required=True, help="Commit message if the worker succeeds")
    parser.add_argument("--lines", default="auto", help="Anchor lines for Stage RAG logging")
    parser.add_argument("--notes", default="", help="Optional Stage RAG notes")
    parser.add_argument("--top", type=int, default=6, help="Stage RAG top-N results")
    args = parser.parse_args()

    git_clean()

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    job_id = f"stage3mgr-{timestamp}"
    plan_id = f"{job_id}-plan"

    print(f"[manager] job_id={job_id} plan_id={plan_id}")

    stage_rag(args.query, plan_id, args.target, args.lines, args.notes, args.top)
    message_file = write_message_file(job_id, args.message)
    print(f"[manager] message file -> {message_file}")

    exit_code = run_worker(message_file, args.target, plan_id)
    events = load_events(plan_id)
    classification, fallback_used, accepted, final_tag = classify(events)
    print(f"[manager] worker exit={exit_code} classification={classification}")

    commit_hash = None
    if accepted:
        commit_hash = commit_changes(args.target, args.commit_msg)
    else:
        git_clean()

    entry = {
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "job_id": job_id,
        "plan_id": plan_id,
        "query": args.query,
        "target_file": args.target,
        "message_file": str(message_file),
        "classification": classification,
        "fallback_used": fallback_used,
        "accepted": accepted,
        "commit_hash": commit_hash,
        "final_tag": final_tag,
        "stage_rag_lines": args.lines,
        "notes": args.notes or None,
        "worker_exit_code": exit_code,
    }
    append_trace(entry)
    print(f"[manager] trace appended -> {TRACE_FILE}")

    git_clean()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
