#!/usr/bin/env python3
"""Stage-5 manager: bounded multi-file literal orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE4_MANAGER = REPO_ROOT / "bin" / "stage4_manager.py"
STAGE_RAG3 = REPO_ROOT / "bin" / "stage_rag3_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "stage5_manager"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
DEFAULT_MAX_OPS = 2
DEFAULT_MAX_TOTAL_LINES = 20


class Stage5Error(SystemExit):
    pass


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("check", True)
    return subprocess.run(cmd, **kwargs)


def ensure_clean_tree() -> None:
    status = run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status.stdout.strip():
        raise Stage5Error("Stage-5 manager requires a clean working tree")


def load_batch(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Stage5Error(f"batch file is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise Stage5Error("batch file must contain a non-empty JSON array")
    entries: list[dict[str, Any]] = []
    for idx, entry in enumerate(data, start=1):
        if not isinstance(entry, dict):
            raise Stage5Error(f"batch entry #{idx} is not an object")
        required = {"query", "target", "message"}
        if not required.issubset(entry):
            missing = required.difference(entry)
            raise Stage5Error(f"batch entry #{idx} missing keys: {', '.join(sorted(missing))}")
        entries.append(entry)
    return entries


def log_trace(entry: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def git_head() -> str:
    proc = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip()


def restore_head(ref: str) -> None:
    run(["git", "reset", "--hard", ref])


def diff_stats(paths: list[str]) -> tuple[int, int]:
    proc = run(["git", "diff", "--numstat", "--"] + paths, capture_output=True, text=True)
    added = deleted = 0
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        if parts[2] not in paths:
            continue
        try:
            added += int(parts[0])
            deleted += int(parts[1])
        except ValueError:
            continue
    return added, deleted


def stage5_manager(args: argparse.Namespace) -> None:
    ensure_clean_tree()
    batch_path = Path(args.batch_file).resolve()
    entries = load_batch(batch_path)
    if len(entries) > args.max_ops:
        raise Stage5Error(f"Stage-5 manager currently supports at most {args.max_ops} operations per batch")

    start_head = git_head()
    job_id = datetime.now(UTC).strftime("stage5-%Y%m%d-%H%M%S")
    modified_files: list[str] = []
    plan_ids: list[str] = []

    try:
        for idx, entry in enumerate(entries, start=1):
            target = entry["target"]
            message = entry["message"]
            query = entry["query"]
            notes = entry.get("notes", "")
            lines = entry.get("lines", "auto")

            plan_id = f"{job_id}-op{idx}"
            plan_ids.append(plan_id)
            rag_cmd = [
                sys.executable,
                str(STAGE_RAG3),
                "--stage",
                "stage5",
                "--plan-id",
                plan_id,
                "--top",
                str(args.rag_top),
                "--selected-path",
                target,
                "--selected-lines",
                str(lines),
                "--notes",
                notes or f"stage5 op {idx}",
                "--",
            ]
            rag_cmd.extend(query.split())
            run(rag_cmd)

            stage4_cmd = [
                sys.executable,
                str(STAGE4_MANAGER),
                "--query",
                query,
                "--target",
                target,
                "--message",
                message,
                "--commit-msg",
                f"stage5-op{idx}",
                "--lines",
                str(lines),
                "--notes",
                notes or "",
                "--no-commit",
            ]
            if entry.get("top"):
                stage4_cmd.extend(["--top", str(entry["top"])])
            if entry.get("window"):
                stage4_cmd.extend(["--window", str(entry["window"])])
            run(stage4_cmd)
            if target not in modified_files:
                modified_files.append(target)

        added, deleted = diff_stats(modified_files)
        if added + deleted > args.max_total_lines:
            raise Stage5Error(
                f"Stage-5 diff exceeded limit ({added + deleted}>{args.max_total_lines}); revert and retry with smaller scope"
            )

        run(["git", "add"] + modified_files)
        run(["git", "commit", "-m", args.commit_msg])
    except Exception as exc:
        restore_head(start_head)
        if isinstance(exc, Stage5Error):
            raise
        raise Stage5Error(str(exc)) from exc

    log_trace(
        {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "job_id": job_id,
            "batch_file": str(batch_path),
            "operations": len(entries),
            "targets": modified_files,
            "plan_ids": plan_ids,
            "commit_msg": args.commit_msg,
            "max_ops": args.max_ops,
            "max_total_lines": args.max_total_lines,
        }
    )
    print(f"[stage5_manager] completed batch {job_id}; committed {args.commit_msg}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage-5 bounded multi-file literal manager")
    parser.add_argument("--batch-file", required=True, help="JSON file describing up to two literal operations")
    parser.add_argument("--commit-msg", required=True, help="Commit message for the combined change")
    parser.add_argument("--max-ops", type=int, default=DEFAULT_MAX_OPS)
    parser.add_argument("--max-total-lines", type=int, default=DEFAULT_MAX_TOTAL_LINES)
    parser.add_argument("--rag-top", type=int, default=6)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        stage5_manager(args)
    except Stage5Error as exc:
        print(f"[stage5_manager] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
