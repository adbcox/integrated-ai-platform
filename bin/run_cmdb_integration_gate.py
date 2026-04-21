#!/usr/bin/env python3
"""Run CMDB integration gate check."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.cmdb_integration_gate import CmdbIntegrationGate, GATE_PASS


def main() -> int:
    gate = CmdbIntegrationGate()
    decision = gate.evaluate()
    print(f"gate_result:   {decision.result}")
    print(f"allowed_class: {decision.allowed_class}")
    print(f"current_phase: {decision.current_phase}")
    print(f"reason:        {decision.reason}")
    print(f"passed:        {decision.passed}")
    return 0 if decision.result == GATE_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
