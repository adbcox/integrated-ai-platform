#!/usr/bin/env python3
"""Expansion closeout ratifier for LAEC1.

Usage: python3 bin/ratify_expansion_closeout.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.expansion_closeout_ratifier import ratify_expansion_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify LAEC1 expansion closeout.")
    parser.add_argument("--artifact-dir", default="artifacts/expansion_closeout")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    artifact = ratify_expansion_closeout(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nCampaign: {artifact.campaign_id}")
    print(f"Decision: {artifact.decision}")
    print(f"All components present: {artifact.all_components_present}")
    print(f"Packets executed: {artifact.packet_count}")
    print()
    print("Component table:")
    for c in artifact.components:
        status = "PRESENT" if c.present else "MISSING"
        print(f"  [{status}] {c.name}: {c.summary}")
    print()
    print(f"Notes: {artifact.notes}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
