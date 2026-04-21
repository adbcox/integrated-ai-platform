#!/usr/bin/env python3
"""LEDT-P4: Prove route decision defaults to local_execute on eligible+ready samples."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_eligibility_contract import LocalExecEligibilityEvaluator, LocalExecEligibilityInput
from framework.local_exec_preflight import LocalExecPreflightEvaluator
from framework.exec_route_decision import ExecRouteDecider

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

SAMPLES = [
    ("LEDT-P4-bounded-a",  2, False, False, False, ["make check"], 2, ["make check"]),
    ("LEDT-P4-bounded-b",  3, False, False, False, ["make check", "pytest"], 3, ["make check", "pytest"]),
    ("LEDT-P4-bounded-c",  1, False, False, False, ["make check"], 1, ["make check"]),
    ("LEDT-P4-ext-api",    1, True,  False, False, ["make check"], 1, ["make check"]),
    ("LEDT-P4-no-val-cmd", 2, False, False, False, [], 2, []),
]


def main() -> None:
    elig_ev = LocalExecEligibilityEvaluator()
    pre_ev = LocalExecPreflightEvaluator()
    decider = ExecRouteDecider()

    decisions = []
    for pid, fsc, ext, broad, infra, vcmds, pre_fsc, pre_vcmds in SAMPLES:
        elig = elig_ev.evaluate(LocalExecEligibilityInput(pid, fsc, ext, broad, infra, vcmds))
        pre = pre_ev.evaluate(pid, pre_fsc, pre_vcmds)
        decisions.append(decider.decide(elig, pre))

    path = decider.emit(decisions, ARTIFACT_DIR)
    local_count = sum(1 for d in decisions if d.route == "local_execute")
    print(f"sample_count:       {len(decisions)}")
    print(f"local_execute:      {local_count}")
    print(f"local_execute_rate: {round(local_count/len(decisions),4)}")
    for d in decisions:
        print(f"  {d.packet_id[:35]}: {d.route}")
    print(f"artifact:           {path}")


if __name__ == "__main__":
    main()
