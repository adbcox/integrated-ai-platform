"""Evidence-gated matrix closeout script for REMAINING-MATRIX-CLOSEOUT-CAMPAIGN-1.

Refuses to emit done-states if packet-4 benchmark evidence is missing or failing.

Usage:
    python3 bin/matrix_closeout_emit.py [--artifact-root PATH] [--bench-artifact PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.matrix_closure_evidence import (
    MatrixItemState,
    derive_campaign_closure,
    emit_closeout_record,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit evidence-driven matrix closeout record")
    parser.add_argument(
        "--artifact-root",
        default=str(REPO_ROOT / "artifacts" / "matrix_closeout"),
    )
    parser.add_argument(
        "--bench-artifact",
        default=str(REPO_ROOT / "artifacts" / "mvp_benchmark" / "mvp_benchmark_result.json"),
    )
    args = parser.parse_args()

    bench_path = Path(args.bench_artifact)
    artifact_dir = Path(args.artifact_root)

    # Evidence gate
    if not bench_path.exists():
        print(f"[EVIDENCE GATE FAIL] Benchmark artifact not found: {bench_path}", file=sys.stderr)
        print("Run `python3 bin/mvp_benchmark_run.py` first.", file=sys.stderr)
        return 1

    try:
        bench = json.loads(bench_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[EVIDENCE GATE FAIL] Cannot read benchmark artifact: {exc}", file=sys.stderr)
        return 1

    if bench.get("outcome") != "pass" or bench.get("total_tasks", 0) != 5 or bench.get("passed", 0) != 5:
        print(
            f"[EVIDENCE GATE FAIL] Benchmark did not pass: "
            f"outcome={bench.get('outcome')}, total={bench.get('total_tasks')}, passed={bench.get('passed')}",
            file=sys.stderr,
        )
        return 1

    items = derive_campaign_closure(bench_artifact_path=bench_path)

    try:
        out_path = emit_closeout_record(
            items,
            artifact_dir=artifact_dir,
            bench_artifact_path=bench_path,
        )
    except RuntimeError as exc:
        print(f"[CLOSEOUT FAILED] {exc}", file=sys.stderr)
        return 1

    print(f"\n{'='*56}")
    print(f"  RMCC1 Matrix Closeout")
    print(f"{'='*56}")
    print(f"  Evidence gate : PASS (5/5 benchmark tasks)")
    print(f"  Artifact      : {out_path}")
    print(f"{'='*56}")
    print()

    _LABEL = {
        "done": "DONE",
        "seed_complete": "SEED_COMPLETE",
        "partial": "PARTIAL",
        "deferred": "DEFERRED",
    }
    for item in items:
        label = _LABEL.get(item.state.value, item.state.value)
        print(f"  [{label:14s}] {item.item_id}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
