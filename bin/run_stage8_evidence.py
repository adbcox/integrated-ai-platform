#!/usr/bin/env python3
"""Stage-8 live evidence orchestrator for Phase 7 gate closure.

Two-pass execution:
  Pass 1: stage7_manager --lane stage8 --stop-after-subplans 1 (produces checkpoint)
  Pass 2: stage7_manager --lane stage8 --resume (resume → resumed_runs > 0)

Then: stage3_manager targeting framework/local_command_runner.py
      (gate_chain_ready: discovery_mode=naming_convention, all 4 gates)

Finally: collect_phase7_evidence.py to update artifact + governance records.
"""

from __future__ import annotations  # PEP-563

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE7_MGR = REPO_ROOT / "bin" / "stage7_manager.py"
STAGE3_MGR = REPO_ROOT / "bin" / "stage3_manager.py"
EVIDENCE_COLLECTOR = REPO_ROOT / "bin" / "collect_phase7_evidence.py"

EVIDENCE_QUERY = ["improve", "LocalCommandRunner", "reliability"]
EVIDENCE_COMMIT_MSG_BASE = "STAGE8-LIVE-EVIDENCE-1: stage8 evidence"
GATE_CHAIN_TARGET = "framework/local_command_runner.py"
GATE_CHAIN_QUERY = "add docstring to LocalCommandRunner run method"
GATE_CHAIN_MESSAGE = (
    "framework/local_command_runner.py::LocalCommandRunner.run "
    "replace exact text 'def run(self, command_name: str) -> LocalCommandResult:' "
    "with 'def run(self, command_name: str) -> LocalCommandResult:  # noqa: D102'"
)
GATE_CHAIN_COMMIT = "STAGE8-LIVE-EVIDENCE-1: inline noqa tag for gate-chain evidence"


def run_cmd(cmd: list[str], *, label: str, dry_run: bool) -> None:
    ts_start = datetime.now(timezone.utc).isoformat()
    print(f"[stage8-evidence] [{ts_start}] START: {label}", flush=True)
    if dry_run:
        print(f"[stage8-evidence] DRY-RUN cmd: {' '.join(cmd)}", flush=True)
        return
    try:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT))
        ts_end = datetime.now(timezone.utc).isoformat()
        if result.returncode != 0:
            print(
                f"[stage8-evidence] [{ts_end}] FAILED: {label} (rc={result.returncode})",
                file=sys.stderr,
                flush=True,
            )
            raise SystemExit(1)
        print(f"[stage8-evidence] [{ts_end}] OK: {label}", flush=True)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[stage8-evidence] ERROR: {label}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage-8 live evidence orchestrator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands that would be run; write no traces.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    plan_id = f"stage8-evidence-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    # Step 1: gate_chain — stage3_manager run (requires clean working tree)
    run_cmd(
        [
            sys.executable, str(STAGE3_MGR),
            "--query", GATE_CHAIN_QUERY,
            "--target", GATE_CHAIN_TARGET,
            "--message", GATE_CHAIN_MESSAGE,
            "--commit-msg", GATE_CHAIN_COMMIT,
        ],
        label="gate_chain_evidence",
        dry_run=args.dry_run,
    )

    # Step 2: stage8 pass 1 — run 1 subplan, pause at checkpoint
    run_cmd(
        [
            sys.executable, str(STAGE7_MGR),
            "--query", *EVIDENCE_QUERY,
            "--plan-id", plan_id,
            "--commit-msg", f"{EVIDENCE_COMMIT_MSG_BASE} pass-1",
            "--lane", "stage8",
            "--stop-after-subplans", "1",
        ],
        label="stage8_pass1",
        dry_run=args.dry_run,
    )

    # Step 3: stage8 pass 2 — resume from checkpoint
    run_cmd(
        [
            sys.executable, str(STAGE7_MGR),
            "--query", *EVIDENCE_QUERY,
            "--plan-id", plan_id,
            "--commit-msg", f"{EVIDENCE_COMMIT_MSG_BASE} pass-2-resume",
            "--lane", "stage8",
            "--resume",
        ],
        label="stage8_pass2_resume",
        dry_run=args.dry_run,
    )

    # Step 4: refresh evidence artifacts
    run_cmd(
        [sys.executable, str(EVIDENCE_COLLECTOR)],
        label="collect_phase7_evidence",
        dry_run=args.dry_run,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
