#!/usr/bin/env python3
"""Read and print CMDB governance authority record."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.cmdb_authority_pilot import CmdbAuthorityPilot


def main() -> int:
    pilot = CmdbAuthorityPilot(governance_dir=Path("governance"))
    rec = pilot.read_authority()
    print(f"current_phase:        {rec.current_phase}")
    print(f"current_phase_status: {rec.current_phase_status}")
    print(f"next_package_class:   {rec.next_package_class}")
    print(f"contract_version:     {rec.contract_version}")
    print(f"phases_count:         {rec.phases_count}")
    print(f"read_at:              {rec.read_at}")
    print(f"gates_summary keys:   {list(rec.gates_summary.keys())[:5]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
