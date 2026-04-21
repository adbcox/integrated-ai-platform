#!/usr/bin/env python3
"""Dry-run first-wave domain branch runners."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST, FirstWaveDomainRunner


def main() -> int:
    runner = FirstWaveDomainRunner()
    for policy in FIRST_WAVE_MANIFEST.policies:
        result = runner.run(policy, dry_run=True, repetitions=2)
        print(f"[{policy.branch_name}] total={result.total_runs} success={result.success_count} fail={result.failure_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
