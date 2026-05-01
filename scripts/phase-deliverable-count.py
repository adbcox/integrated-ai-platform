#!/usr/bin/env python3
"""
Print deliverable counts for a given phase from PROJECT_FRAMEWORK.md.

Surface-format helper: removes the off-by-one risk in hand-written
"X of N tasks" / "X of M deliverables" lines. Parses §N "Phase NN —
current state" deliverable tables (any phase) and reports DONE / total.

Usage:
    python3 scripts/phase-deliverable-count.py 16

Output (machine-readable line + human breakdown):

    PHASE 16 STATE: 6 of 14 deliverables complete

    DONE        D-16-02      a3c198c
    DONE        D-16-02.0.5  c642034
    ...
    NOT STARTED D-16-09      C4 auto-architecture

Exit 0 always; emits to stderr if the requested phase isn't found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FRAMEWORK = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"

ROW = re.compile(r"^\|\s*(D-\d+-[\w.]+)\s*:\s*(.*?)\s*\|\s*([\w \-]+?)\s*\|\s*(.*?)\s*\|\s*$")


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("Usage: phase-deliverable-count.py <phase-number>")
    phase = int(sys.argv[1])

    rows = []
    for line in FRAMEWORK.read_text().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        del_id, title, status, ref = m.groups()
        if not del_id.startswith(f"D-{phase}-"):
            continue
        rows.append((del_id, title, status.strip(), ref.strip()))

    if not rows:
        print(f"No deliverables for Phase {phase}", file=sys.stderr)
        return 0

    done = sum(1 for r in rows if r[2].upper() == "DONE")
    print(f"PHASE {phase} STATE: {done} of {len(rows)} deliverables complete")
    print()
    width = max(len(r[2]) for r in rows)
    for del_id, title, status, ref in rows:
        print(f"  {status.ljust(width)}  {del_id.ljust(12)}  {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
