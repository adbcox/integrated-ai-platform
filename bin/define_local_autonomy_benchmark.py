#!/usr/bin/env python3
"""LACE1-P9: Emit the LACE1 local autonomy benchmark pack artifact."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_autonomy_benchmark_pack import (
    LACE1_TASK_PACK,
    emit_benchmark_pack,
    validate_acceptance_greps,
)

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"


def main() -> None:
    bad_greps = validate_acceptance_greps(LACE1_TASK_PACK)
    if bad_greps:
        print(f"ERROR: invalid acceptance_grep patterns in tasks: {bad_greps}", file=sys.stderr)
        sys.exit(1)

    path = emit_benchmark_pack(LACE1_TASK_PACK, ARTIFACT_DIR)
    print(f"benchmark_pack emitted: {path}")
    print(f"  tasks: {len(LACE1_TASK_PACK)}")

    from framework.local_autonomy_benchmark_pack import _kind_summary
    for kind, count in sorted(_kind_summary(LACE1_TASK_PACK).items()):
        print(f"  {kind}: {count}")


if __name__ == "__main__":
    main()
