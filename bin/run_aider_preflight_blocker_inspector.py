#!/usr/bin/env python3
"""Run preflight blocker inspector for APCC1-P1.

Usage: python3 bin/run_aider_preflight_blocker_inspector.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_preflight_blocker_inspector import inspect_preflight_blockers


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Aider preflight blocker injection paths.")
    parser.add_argument("--artifact-dir", default="artifacts/preflight_blocker_inspector")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    artifact = inspect_preflight_blockers(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print("\n=== Aider Preflight Blocker Inspector ===")
    print(f"  total_blockers:      {artifact.total_blockers}")
    print(f"  injectable:          {artifact.injectable_blockers}")
    print(f"  non_injectable:      {artifact.non_injectable_blockers}")
    print(f"  preflight_checker:   {artifact.preflight_checker_constructor}")
    print(f"  runtime_adapter:     {artifact.runtime_adapter_constructor}")
    print(f"  permission_gate:     {artifact.permission_gate_interface}")
    print(f"  config_surface:      {artifact.config_surface_interface}")
    print()
    print(f"{'Blocker':<30} {'Injectable':<12} {'Injection Path'}")
    print("-" * 90)
    for r in artifact.blocker_records:
        inj = "YES" if r.injection_path != "NO_INJECTABLE_PATH" else "NO"
        print(f"  {r.blocker_name:<28} {inj:<12} {r.injection_path}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
