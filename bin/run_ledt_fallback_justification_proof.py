#!/usr/bin/env python3
"""LEDT-P5: Produce fallback justification samples with distinct classes."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_eligibility_contract import LocalExecEligibilityEvaluator, LocalExecEligibilityInput
from framework.local_exec_preflight import LocalExecPreflightEvaluator
from framework.exec_route_decision import ExecRouteDecider
from framework.fallback_justification import FallbackJustificationWriter

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def _make_fallback(pid, ext=False, fsc=2, vcmds=None):
    _vcmds = ["make check"] if vcmds is None else vcmds
    elig = LocalExecEligibilityEvaluator().evaluate(
        LocalExecEligibilityInput(pid, fsc, ext, False, False, _vcmds)
    )
    pre = LocalExecPreflightEvaluator().evaluate(pid, fsc, _vcmds)
    return ExecRouteDecider().decide(elig, pre)


def main() -> None:
    writer = FallbackJustificationWriter()

    d1 = _make_fallback("aider-missing", ext=True)
    d2 = _make_fallback("scope-exceeded", fsc=12)
    d3 = _make_fallback("no-validation", vcmds=[])

    records = [
        writer.record(d1, "tool_unavailable", "aider package not found on sys.path during preflight C1 check", True,
                      "install aider via pip before running local execution"),
        writer.record(d2, "scope_exceeded", f"file_scope_count={12} exceeds max 5 allowed by eligibility contract", True,
                      "split packet into sub-packets each touching <= 5 files"),
        writer.record(d3, "validation_failure", "no validation_commands specified in packet input; overall_ready=False", True,
                      "add at least one validation command (e.g. make check) to packet spec"),
    ]

    path = writer.emit(records, ARTIFACT_DIR)
    print(f"sample_count:  {len(records)}")
    for r in records:
        print(f"  {r.packet_id}: class={r.justification_class} avoidable={r.avoidable_in_future}")
    print(f"artifact:      {path}")


if __name__ == "__main__":
    main()
