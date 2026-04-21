#!/usr/bin/env python3
"""LACE2-P7: Emit the real-file benchmark pack artifact."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.real_file_benchmark_pack import LACE2_REAL_FILE_PACK, emit_real_file_pack, validate_real_file_greps

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    bad = validate_real_file_greps(LACE2_REAL_FILE_PACK)
    if bad:
        print(f"ERROR: bad acceptance_grep in tasks: {bad}", file=sys.stderr)
        sys.exit(1)
    path = emit_real_file_pack(LACE2_REAL_FILE_PACK, ARTIFACT_DIR)
    print(f"pack_id:      LACE2-REAL-FILE-BENCHMARK-PACK")
    print(f"task_count:   {len(LACE2_REAL_FILE_PACK)}")
    kinds = {}
    for t in LACE2_REAL_FILE_PACK:
        kinds[t.task_kind] = kinds.get(t.task_kind, 0) + 1
    print(f"kind_summary: {kinds}")
    print(f"artifact:     {path}")


if __name__ == "__main__":
    main()
