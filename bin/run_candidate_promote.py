#!/usr/bin/env python3
"""Candidate-lane promotion orchestrator for Phase 7 gate closure.

Runs 4 sequential manager4 candidate-lane jobs, each performing:
  from __future__ import annotations  ->  from __future__ import annotations  # PEP-563

Then invokes collect_phase7_evidence.py and reports whether all_ready is true.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANAGER4 = REPO_ROOT / "bin" / "manager4.py"
EVIDENCE_COLLECTOR = REPO_ROOT / "bin" / "collect_phase7_evidence.py"
TRACE_FILE = REPO_ROOT / "artifacts" / "manager4" / "traces.jsonl"

LITERAL_OLD = "from __future__ import annotations"
LITERAL_NEW = "from __future__ import annotations  # PEP-563"

CANDIDATE_RUNS = [
    {
        "target": "bin/collect_phase7_evidence.py",
        "commit_msg": "STAGE8-CANDIDATE-PROMOTE-1: candidate run 1 annotate annotations import",
    },
    {
        "target": "bin/developer_assistance.py",
        "commit_msg": "STAGE8-CANDIDATE-PROMOTE-1: candidate run 2 annotate annotations import",
    },
    {
        "target": "bin/run_stage8_evidence.py",
        "commit_msg": "STAGE8-CANDIDATE-PROMOTE-1: candidate run 3 annotate annotations import",
    },
    {
        "target": "bin/run_baseline_validation.py",
        "commit_msg": "STAGE8-CANDIDATE-PROMOTE-1: candidate run 4 annotate annotations import",
    },
]


def build_message(target: str) -> str:
    fname = Path(target).name
    return (
        f"{fname}:: replace exact text "
        f"'from __future__ import annotations' "
        f"with 'from __future__ import annotations  # PEP-563'"
    )


def _check_clean_tree() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.stdout.strip():
        print(
            f"[promote] ERROR: working tree is not clean:\n{result.stdout}",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _run_cmd(cmd: list[str], *, label: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[promote] DRY-RUN: {' '.join(cmd)}", flush=True)
        return
    print(f"[promote] START: {label}", flush=True)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print(
            f"[promote] FAILED: {label} (rc={result.returncode})",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1)
    print(f"[promote] OK: {label}", flush=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Candidate-lane promotion orchestrator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands and expected run set; make no changes; exit 0.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if not args.dry_run:
        _check_clean_tree()

    print(f"[promote] {'DRY-RUN ' if args.dry_run else ''}candidate runs: {len(CANDIDATE_RUNS)}", flush=True)

    for i, run in enumerate(CANDIDATE_RUNS, start=1):
        target = run["target"]
        commit_msg = run["commit_msg"]
        message = build_message(target)

        cmd = [
            sys.executable, str(MANAGER4),
            "--query", "annotate annotations import in bin target file",
            "--target", target,
            "--message", message,
            "--commit-msg", commit_msg,
            "--lane", "candidate",
            "--stage", "stage3",
        ]

        _run_cmd(cmd, label=f"candidate run {i}: {target}", dry_run=args.dry_run)

    # Refresh evidence artifacts
    _run_cmd(
        [sys.executable, str(EVIDENCE_COLLECTOR)],
        label="collect_phase7_evidence",
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("[promote] DRY-RUN complete.", flush=True)
        return 0

    # Report results
    try:
        ev = json.loads(REPO_ROOT.joinpath("artifacts/phase7_evidence/latest.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[promote] ERROR reading evidence: {exc}", file=sys.stderr)
        return 1

    all_ready = ev.get("all_ready", False)
    missing = ev.get("missing_gates", [])
    print(f"[promote] all_ready: {all_ready}", flush=True)
    print(f"[promote] missing_gates: {missing}", flush=True)

    if not all_ready:
        print("[promote] FAIL: all_ready is still False", file=sys.stderr)
        return 1

    print("[promote] Phase 7 CLOSED — all 9 v8 gates READY", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
