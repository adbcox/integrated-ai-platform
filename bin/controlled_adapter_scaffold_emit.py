"""Emit controlled adapter scaffold plan (dry-run or full)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.controlled_adapter_scaffold import ControlledAdapterScaffold, emit_scaffold_plan
from framework.adapter_readiness_stress import AdapterReadinessStressHarness, emit_stress_result
from framework.adapter_campaign_pre_authorizer import pre_authorize_adapter_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit controlled adapter scaffold plan")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing artifacts")
    args = parser.parse_args()

    stress_result = None
    pre_auth = None

    try:
        stress_result = AdapterReadinessStressHarness().run()
    except Exception as e:
        print(f"  [warn] stress_result unavailable: {e}")

    try:
        pre_auth = pre_authorize_adapter_campaign()
    except Exception as e:
        print(f"  [warn] pre_auth unavailable: {e}")

    scaffold = ControlledAdapterScaffold()
    plan = scaffold.build(stress_result=stress_result, pre_auth=pre_auth)

    print(f"\n{'='*55}")
    print(f"  Controlled Adapter Scaffold")
    print(f"{'='*55}")
    print(f"  Decision     : {plan.scaffold_decision}")
    print(f"  Gates passed : {plan.gates_passed}/{plan.gates_total}")
    print(f"  Campaign ID  : {plan.campaign_id or 'n/a'}")
    print(f"{'='*55}")
    for g in plan.gates:
        status = "PASS" if g.passed else "FAIL"
        print(f"  [{status}] {g.gate_name}: {g.detail}")
    if plan.defer_reasons:
        print(f"{'='*55}")
        print(f"  Defer reasons:")
        for r in plan.defer_reasons:
            print(f"    - {r}")
    print(f"{'='*55}")

    if args.dry_run:
        print("  [dry-run] artifact not written")
    else:
        artifact_dir = REPO_ROOT / "artifacts" / "controlled_adapter_scaffold"
        out_path = emit_scaffold_plan(plan, artifact_dir=artifact_dir)
        print(f"  Artifact: {out_path}")

    print(f"{'='*55}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
