#!/usr/bin/env python3
"""Stage-4 manager orchestrator for bounded multi-line literal edits."""

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
STAGE_RAG2 = REPO_ROOT / "bin" / "stage_rag2_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "stage4_manager"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
EVENT_LOG = REPO_ROOT / "artifacts" / "micro_runs" / "events.jsonl"
DEFAULT_MIN_LINES = 3
DEFAULT_MAX_LINES = 8
HARNESS_TARGETS = {
    "bin/aider_micro.sh",
    "bin/aider_loop.sh",
    "bin/stage3_manager.py",
    "bin/stage4_manager.py",
    "bin/manager3.py",
}
MESSAGE_LITERAL_RE = re.compile(r"replace exact text '(.+?)' with '(.+?)'", re.DOTALL)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("check", True)
    return subprocess.run(cmd, **kwargs)


def git_clean() -> None:
    result = run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    if result.stdout.strip():
        raise SystemExit("Working tree must be clean before running stage4_manager")


def stage_rag(query: str, plan_id: str, target: str, lines: str, notes: str, top: int, window: int) -> None:
    if not STAGE_RAG2.exists():
        raise SystemExit(f"Missing Stage RAG-2 helper: {STAGE_RAG2}")
    tokens = shlex.split(query)
    if not tokens:
        raise SystemExit("Query must produce at least one token")
    cmd = [
        sys.executable,
        str(STAGE_RAG2),
        "--stage",
        "stage4",
        "--plan-id",
        plan_id,
        "--top",
        str(top),
        "--window",
        str(window),
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
    path = Path(tempfile.gettempdir()) / f"stage4_job_{job_id}.msg"
    path.write_text(message.strip() + "\n", encoding="utf-8")
    return path


def _extract_literals(message: str) -> tuple[str | None, str | None]:
    match = MESSAGE_LITERAL_RE.search(message)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _line_count(text: str | None) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def _ensure_literal_bounds(message: str, target_contents: str, min_lines: int, max_lines: int) -> None:
    old_literal, new_literal = _extract_literals(message)
    if not old_literal or not new_literal:
        raise SystemExit("Stage 4 requires explicit literal replacement instructions with quoted old/new blocks")
    largest = max(_line_count(old_literal), _line_count(new_literal))
    if largest < min_lines:
        raise SystemExit(f"Stage-4 literal spans must cover at least {min_lines} lines (found {largest})")
    if largest > max_lines:
        raise SystemExit(f"Stage-4 literal spans must stay within {max_lines} lines (found {largest})")
    if old_literal not in target_contents:
        raise SystemExit("Old literal block not found in target file; re-sync anchor or update lines")


def _load_events(plan_id: str) -> list[dict]:
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


def _classify(events: list[dict]) -> tuple[str, bool, bool, str | None, str | None, str | None, int]:
    fallback_tags = {"literal_fallback_start", "literal_fallback_applied"}
    fallback_used = any(evt.get("tag") in fallback_tags for evt in events)
    literal_diff_flag = any(evt.get("tag") == "literal_diff_allowed" for evt in events)
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
            if literal_diff_flag:
                classification = "literal_diff_allowed"
                final_tag = "literal_diff_allowed"
            elif fallback_used:
                classification = "aider_exit_recovered"
            else:
                classification = "accepted_change"
        else:
            classification = final_tag or "other_clean_rejection"
    return classification, fallback_used, accepted, final_tag, final_status, final_note, len(events)


def _diff_stats(target: str) -> tuple[int, int]:
    proc = run(["git", "diff", "--numstat"], capture_output=True, text=True)
    added = 0
    deleted = 0
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        add, delete, path = parts[0], parts[1], parts[2]
        if path != target:
            raise SystemExit(f"Stage-4 run touched unexpected file: {path}")
        try:
            added = int(add)
            deleted = int(delete)
        except ValueError:
            continue
    return added, deleted


def append_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def commit_changes(target: str, commit_msg: str) -> str | None:
    status = run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    if status.stdout.strip():
        run(["git", "add", target])
        run(["git", "commit", "-m", commit_msg])
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return head.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage-4 bounded multi-line manager")
    parser.add_argument("--query", required=True, help="Stage RAG query")
    parser.add_argument("--target", required=True, help="Target file")
    parser.add_argument("--message", required=True, help="Literal instruction message")
    parser.add_argument("--commit-msg", required=True, help="Commit message for accepted change")
    parser.add_argument("--lines", default="auto", help="Anchor lines for logging")
    parser.add_argument("--notes", default="", help="Optional Stage RAG notes")
    parser.add_argument("--top", type=int, default=6, help="Stage RAG-2 top-N results")
    parser.add_argument("--window", type=int, default=20, help="Stage RAG-2 context window")
    parser.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--max-total-lines", type=int, default=12, help="Maximum total changed lines (add+delete)")
    parser.add_argument("--no-commit", action="store_true", help="Leave accepted changes unstaged for a parent manager to commit")
    parser.add_argument(
        "--allow-literal-diff",
        action="store_true",
        help="Treat literal_replace_diff guard hits as accepted (for orchestrators that post-validate diffs)",
    )
    args = parser.parse_args()

    if args.target in HARNESS_TARGETS:
        raise SystemExit(f"Stage-4 manager refuses to edit running harness file: {args.target}")

    git_clean()

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    job_id = f"stage4mgr-{timestamp}"
    plan_id = f"{job_id}-plan"

    target_path = (REPO_ROOT / args.target).resolve()
    if not target_path.exists():
        raise SystemExit(f"Target file not found: {args.target}")

    stage_rag(args.query, plan_id, args.target, args.lines, args.notes, args.top, args.window)
    message_file = write_message_file(job_id, args.message)

    try:
        target_contents = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Failed to read target file {target_path}: {exc}") from exc

    _ensure_literal_bounds(args.message, target_contents, args.min_lines, args.max_lines)

    env = os.environ.copy()
    env["AIDER_MICRO_STAGE"] = "stage4"
    env["AIDER_MICRO_PLAN_ID"] = plan_id
    if args.allow_literal_diff:
        env["AIDER_MICRO_ALLOW_LITERAL_DIFF"] = "1"
    else:
        env.pop("AIDER_MICRO_ALLOW_LITERAL_DIFF", None)
    cmd = [
        "make",
        "aider-micro-safe",
        f"AIDER_MICRO_MESSAGE_FILE={message_file}",
        f"AIDER_MICRO_FILES={args.target}",
    ]
    exit_code = subprocess.run(cmd, env=env).returncode

    events = _load_events(plan_id)
    (
        classification,
        fallback_used,
        accepted,
        final_tag,
        final_status,
        final_note,
        event_count,
    ) = _classify(events)

    diff_added = 0
    diff_deleted = 0
    if not accepted and classification == "literal_replace_diff" and args.allow_literal_diff:
        classification = "literal_diff_allowed"
        accepted = True

    if accepted:
        diff_added, diff_deleted = _diff_stats(args.target)
        if diff_added + diff_deleted > args.max_total_lines:
            run(["git", "restore", "--staged", args.target])
            run(["git", "checkout", "--", args.target])
            git_clean()
            raise SystemExit(
                f"Stage-4 diff exceeded safe limit ({diff_added + diff_deleted}>{args.max_total_lines}). Run again with smaller scope."
            )
        if args.no_commit:
            commit_hash = None
            # leave changes in the working tree for a parent orchestration layer
        else:
            commit_hash = commit_changes(args.target, args.commit_msg)
    else:
        commit_hash = None
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
        "diff_added": diff_added,
        "diff_deleted": diff_deleted,
        "literal_min_lines": args.min_lines,
        "literal_max_lines": args.max_lines,
        "notes": args.notes or None,
        "worker_exit_code": exit_code,
    }
    append_trace(entry)
    print(f"[stage4_manager] trace appended -> {TRACE_FILE}")
    if not args.no_commit:
        git_clean()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
