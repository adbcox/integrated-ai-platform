#!/usr/bin/env python3
"""Manager-2.1 orchestrator for Stage-3 literal/comment worker jobs."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
import re
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
    # Explicit classes requested for Manager-2 telemetry
    "literal_replace_missing_old": "literal_replace_missing_old",
    "literal_shell_risky": "literal_shell_risky",
    "prompt_contract_rejection": "prompt_contract_rejection",
    "fallback_blocked_running_script": "fallback_blocked_running_script",
    "literal_replace_fallback": "clean_literal_replace_failure",
    # Supplemental tags that should still appear distinctly in traces
    "missing_file_ref": "missing_file_ref",
    "missing_anchor": "missing_anchor",
    "comment_scope": "clean_comment_scope_rejection",
    "repo_unwritable": "external_repo_writability_block",
}

FALLBACK_TAGS = {"literal_fallback_start", "literal_fallback_applied"}
HARNESS_TARGETS = {
    "bin/aider_micro.sh",
    "bin/aider_loop.sh",
    "bin/stage3_manager.py",
}


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


def classify(events: list[dict]) -> tuple[
    str,
    bool,
    bool,
    str | None,
    str | None,
    str | None,
    int,
]:
    fallback_used = any(evt.get("tag") in FALLBACK_TAGS for evt in events)
    final = None
    for evt in reversed(events):
        if evt.get("status") in {"success", "failure"}:
            final = evt
            break

    accepted = False
    classification = "unknown"
    final_tag = None
    final_status = None
    final_note = None
    if final:
        final_status = final.get("status")
        final_tag = final.get("tag") or "completed"
        final_note = final.get("note")
        if final_status == "success":
            accepted = True
            classification = "aider_exit_recovered" if fallback_used else "accepted_change"
        else:
            classification = _classify_failure(final_tag, fallback_used)
    else:
        classification = "unknown"

    return (
        classification,
        fallback_used,
        accepted,
        final_tag,
        final_status,
        final_note,
        len(events),
    )


def _classify_failure(final_tag: str | None, fallback_used: bool) -> str:
    if not final_tag:
        return "other_clean_rejection"

    if final_tag == "aider_exit":
        # In Stage-3 the literal fallback is blocked when the target file is the
        # currently running script (e.g. aider_micro.sh). Treat that uniquely.
        return "fallback_blocked_running_script"

    if final_tag in {"literal_replace_fallback", "literal_fallback_start", "literal_fallback_applied"}:
        return "clean_literal_replace_failure"

    if final_tag == "no_change":
        return "clean_literal_replace_failure"

    if final_tag == "literal_shell_risky":
        return "literal_shell_risky"

    mapped = FAILURE_CLASS_MAP.get(final_tag)
    if mapped:
        return mapped

    return "other_clean_rejection"


def commit_changes(target: str, commit_msg: str) -> str | None:
    status = run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    if status.stdout.strip():
        run(["git", "add", target])
        run(["git", "commit", "-m", commit_msg])
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return head.stdout.strip()


def append_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _extract_old_literal(message: str) -> str | None:
    match = re.search(r"replace exact text '(.+?)' with '(.+?)'", message, re.DOTALL)
    if match:
        return match.group(1)
    return None


def _preflight_literal_check(target_path: Path, message: str) -> bool:
    old_literal = _extract_old_literal(message)
    if not old_literal:
        return False
    try:
        contents = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Failed to read target file {target_path}: {exc}") from exc
    return old_literal not in contents


def _record_skip(job_id: str, plan_id: str, args, *, classification: str, note: str, message_file: Path | None) -> int:
    entry = {
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "job_id": job_id,
        "plan_id": plan_id,
        "query": args.query,
        "target_file": args.target,
        "message_file": str(message_file) if message_file else None,
        "classification": classification,
        "fallback_used": False,
        "accepted": False,
        "commit_hash": None,
        "final_tag": "preflight",
        "final_status": "failure",
        "final_note": note,
        "event_count": 0,
        "stage_rag_lines": args.lines,
        "notes": args.notes or None,
        "worker_exit_code": None,
    }
    append_trace(entry)
    print(f"[manager] skipping worker: {classification} ({note})")
    git_clean()
    return 0


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

    target_path = (REPO_ROOT / args.target).resolve()
    if not target_path.exists():
        raise SystemExit(f"Target file not found: {args.target}")

    stage_rag(args.query, plan_id, args.target, args.lines, args.notes, args.top)
    message_file = write_message_file(job_id, args.message)
    print(f"[manager] message file -> {message_file}")

    if args.target in HARNESS_TARGETS:
        return _record_skip(
            job_id,
            plan_id,
            args,
            classification="routed_to_codex",
            note="target is a running harness; route to Codex",
            message_file=message_file,
        )

    if _preflight_literal_check(target_path, args.message):
        return _record_skip(
            job_id,
            plan_id,
            args,
            classification="literal_replace_missing_old",
            note="preflight literal not present",
            message_file=message_file,
        )

    exit_code = run_worker(message_file, args.target, plan_id)
    events = load_events(plan_id)
    (
        classification,
        fallback_used,
        accepted,
        final_tag,
        final_status,
        final_note,
        event_count,
    ) = classify(events)
    print(
        "[manager] worker exit=%s classification=%s final_tag=%s"
        % (exit_code, classification, final_tag)
    )

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
        "final_status": final_status,
        "final_note": final_note,
        "event_count": event_count,
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
