#!/usr/bin/env python3
"""Run RM-OPS-007 archive convergence across canonical and derived roadmap surfaces."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.rm_ops007_archive_convergence import (
    archive_converge_items,
    collect_item_status,
    sync_registry_and_sync_state,
)
ITEMS_DIR = REPO_ROOT / "docs/roadmap/items"
REGISTRY = REPO_ROOT / "docs/roadmap/data/roadmap_registry.yaml"
SYNC_STATE = REPO_ROOT / "docs/roadmap/data/sync_state.yaml"
REPORT_PATH = REPO_ROOT / "artifacts/operations/rm_ops007_archive_convergence_report.json"


def run_cmd(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RM-OPS-007 archive convergence")
    parser.add_argument("--dry-run", action="store_true", help="Compute decisions without writing changes")
    parser.add_argument("--skip-derived-refresh", action="store_true", help="Skip compute_next_pull refresh")
    args = parser.parse_args()

    today_iso = "2026-04-23"
    decisions, archived_ids = archive_converge_items(
        ITEMS_DIR,
        apply_changes=not args.dry_run,
        today_iso=today_iso,
    )

    if not args.dry_run:
        item_status = collect_item_status(ITEMS_DIR)
        sync_registry_and_sync_state(
            registry_path=REGISTRY,
            sync_state_path=SYNC_STATE,
            item_status_by_id=item_status,
        )

        derived_refresh_code = 0
        if not args.skip_derived_refresh:
            derived_refresh_code = run_cmd(["python3", "bin/compute_next_pull.py"])

        report = {
            "generated_at": "2026-04-23T00:00:00Z",
            "run_kind": "rm_ops007_archive_convergence",
            "dry_run": False,
            "archived_count": len(archived_ids),
            "archived_ids": archived_ids,
            "held_ids": [d.item_id for d in decisions if d.action == "hold"],
            "decisions": [d.to_dict() for d in decisions],
            "derived_refresh_code": derived_refresh_code,
        }
    else:
        report = {
            "generated_at": "2026-04-23T00:00:00Z",
            "run_kind": "rm_ops007_archive_convergence",
            "dry_run": True,
            "archived_count": len(archived_ids),
            "archived_ids": archived_ids,
            "held_ids": [d.item_id for d in decisions if d.action == "hold"],
            "decisions": [d.to_dict() for d in decisions],
            "derived_refresh_code": None,
        }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
