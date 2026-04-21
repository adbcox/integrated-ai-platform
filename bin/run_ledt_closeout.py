#!/usr/bin/env python3
"""LEDT-P12: Emit LEDT_closeout.json."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.ledt_expansion_closeout_ratifier import LEDTExpansionCloseoutRatifier
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def main():
    ratifier = LEDTExpansionCloseoutRatifier()
    record = ratifier.ratify()
    path = ratifier.emit(record, ARTIFACT_DIR)
    print(f"closeout_id:              {record.closeout_id}")
    print(f"campaign_verdict:         {record.campaign_verdict}")
    print(f"packets_completed:        {record.packets_completed}/{record.packets_expected}")
    print(f"artifacts_present:        {record.artifacts_present}/{record.artifacts_expected}")
    print(f"modules_importable:       {record.modules_importable}/{record.modules_expected}")
    print(f"transition_verdict:       {record.transition_verdict}")
    print(f"what_was_built:           {len(record.what_was_built)}")
    print(f"known_limitations:        {len(record.known_limitations)}")
    print(f"when_claude_allowed:      {len(record.when_claude_execution_allowed)}")
    print(f"what_remains_unproven:    {len(record.what_remains_unproven)}")
    print(f"artifact:                 {path}")

if __name__ == "__main__":
    main()
