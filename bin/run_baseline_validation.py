#!/usr/bin/env python3
"""Baseline validation runner for RM-CORE-006.

Runs check and quick via LocalCommandRunner and writes the canonical
baseline artifact at artifacts/baseline_validation/latest.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.local_command_runner import LocalCommandRunner

BASELINE_ARTIFACT_ROOT: Path = REPO_ROOT / "artifacts" / "baseline_validation"
BASELINE_LATEST: Path = BASELINE_ARTIFACT_ROOT / "latest.json"
DEFINITION_OF_DONE_REF: str = "docs/execution/definition_of_done.md"
BASELINE_SCHEMA_VERSION: int = 1
COMMANDS_TO_RUN: list[str] = ["check", "quick"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _head_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def run_baseline_validation(
    *,
    dry_run: bool = False,
    write_artifact: bool = True,
) -> dict[str, Any]:
    runner = LocalCommandRunner(cwd=REPO_ROOT)
    command_entries: dict[str, Any] = {}

    for cmd in COMMANDS_TO_RUN:
        if dry_run:
            entry = {
                "command_name": cmd,
                "argv": f"[dry-run] {cmd}",
                "return_code": 0,
                "success": True,
                "duration_ms": 0,
                "stdout_head": "[dry-run]",
                "stderr_head": "",
                "started_at": _iso_now(),
                "completed_at": _iso_now(),
            }
        else:
            result = runner.run(cmd)
            entry = {
                "command_name": result.command_name,
                "argv": result.argv,
                "return_code": result.return_code,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "stdout_head": result.stdout[:2000],
                "stderr_head": result.stderr[:500],
                "started_at": result.started_at,
                "completed_at": result.completed_at,
            }
        command_entries[cmd] = entry

    all_passed = all(e["success"] for e in command_entries.values())
    payload: dict[str, Any] = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "generated_at": _iso_now(),
        "baseline_commit": _head_commit(),
        "definition_of_done_ref": DEFINITION_OF_DONE_REF,
        "dry_run": dry_run,
        "commands": command_entries,
        "all_passed": all_passed,
        "definition_of_done_met": all_passed,
    }

    if write_artifact:
        BASELINE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        BASELINE_LATEST.write_text(
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline validation and write artifact.")
    parser.add_argument("--dry-run", action="store_true", help="Use synthetic pass entries; no real make calls")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = run_baseline_validation(dry_run=args.dry_run, write_artifact=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["all_passed"] else 1)
