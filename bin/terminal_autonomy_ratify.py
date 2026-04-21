"""Emit terminal autonomy ratification record (dry-run or full)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.terminal_autonomy_ratifier import TerminalAutonomyRatifier, emit_terminal_ratification
from framework.adapter_readiness_stress import AdapterReadinessStressHarness
from framework.controlled_adapter_scaffold import ControlledAdapterScaffold
from framework.adapter_campaign_pre_authorizer import pre_authorize_adapter_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit terminal autonomy ratification record")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing artifacts")
    args = parser.parse_args()

    stress_result = None
    scaffold_plan = None
    pre_auth = None
    ratification_artifact = None

    try:
        stress_result = AdapterReadinessStressHarness().run()
    except Exception as e:
        print(f"  [warn] stress_result unavailable: {e}")

    try:
        pre_auth = pre_authorize_adapter_campaign()
        ratification_artifact = getattr(pre_auth, "_ratification_artifact", None)
    except Exception as e:
        print(f"  [warn] pre_auth unavailable: {e}")

    try:
        scaffold_plan = ControlledAdapterScaffold().build(
            stress_result=stress_result, pre_auth=pre_auth
        )
    except Exception as e:
        print(f"  [warn] scaffold_plan unavailable: {e}")

    ratifier = TerminalAutonomyRatifier()
    record = ratifier.ratify(
        stress_result=stress_result,
        scaffold_plan=scaffold_plan,
        ratification_artifact=ratification_artifact,
    )

    print(f"\n{'='*60}")
    print(f"  Terminal Autonomy Ratification")
    print(f"{'='*60}")
    print(f"  Terminal verdict   : {record.terminal_verdict}")
    print(f"  Criteria passed    : {record.criteria_passed}/{record.criteria_total}")
    print(f"  Campaign ID        : {record.campaign_id or 'n/a'}")
    print(f"  Ratified at        : {record.ratified_at}")
    print(f"{'='*60}")
    for c in record.criteria:
        status = "PASS" if c.passed else "FAIL"
        print(f"  [{status}] {c.criterion_name}: {c.detail}")
    if record.blocking_reasons:
        print(f"{'='*60}")
        print(f"  Blocking reasons:")
        for r in record.blocking_reasons:
            print(f"    - {r}")
    print(f"{'='*60}")

    if args.dry_run:
        print("  [dry-run] artifact not written")
    else:
        artifact_dir = REPO_ROOT / "artifacts" / "terminal_ratification"
        out_path = emit_terminal_ratification(record, artifact_dir=artifact_dir)
        print(f"  Artifact: {out_path}")

    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
