#!/usr/bin/env python3
"""LEDT-P8: Emit planner preference records."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.planner_preference_schema import PlannerPreferenceBuilder
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def main():
    b = PlannerPreferenceBuilder()
    records = [
        b.build("LEDT", "LACE2 proved real bounded local execution; LEDT adds routing machinery to make local the default.",
                ["LACE2_closeout.json", "lace2_autonomy_proof_ratification.json",
                 "artifacts/expansion/LEDT/local_first_proof.json"],
                claude_allowed=False),
        b.build("LEDT-exception", "Claude execution permitted only under explicit disqualifying conditions.",
                ["LACE2_closeout.json", "route_decision_proof.json"],
                claude_allowed=True,
                claude_conditions=[
                    "aider and framework.code_executor both unavailable (preflight C2 failed)",
                    "packet file_scope_count > 5 and task cannot be split",
                    "explicit hard_stop condition identified in eligibility check",
                ]),
    ]
    path = b.emit_batch(records, ARTIFACT_DIR)
    lf_rate = sum(1 for r in records if r.default_executor_preference == "local_first") / len(records)
    print(f"sample_count:     {len(records)}")
    print(f"local_first_rate: {lf_rate}")
    for r in records:
        print(f"  {r.campaign_id}: default={r.default_executor_preference} claude_allowed={r.claude_execution_allowed}")
    print(f"artifact:         {path}")

if __name__ == "__main__":
    main()
