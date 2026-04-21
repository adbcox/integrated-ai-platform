#!/usr/bin/env python3
"""LEDT-P10: Run 5-sample proof showing local_execute is default."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.local_first_proof_harness import LocalFirstProofHarness
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

SAMPLES = [
    {"packet_id": "add-seam-test-repair-policy",
     "description": "Add seam test for repair policy proof",
     "file_scope_count": 2, "has_external_api_calls": False,
     "requires_broad_redesign": False, "requires_live_infra_touch": False,
     "validation_commands": ["make check", "pytest tests/test_repair_policy_seam.py -v"]},
    {"packet_id": "wire-retrieval-enrichment-proof",
     "description": "Wire retrieval enrichment into live proof path",
     "file_scope_count": 3, "has_external_api_calls": False,
     "requires_broad_redesign": False, "requires_live_infra_touch": False,
     "validation_commands": ["make check", "pytest tests/test_live_retrieval_proof_seam.py -v"]},
    {"packet_id": "emit-typed-run-receipt",
     "description": "Emit typed local run receipt per execution attempt",
     "file_scope_count": 2, "has_external_api_calls": False,
     "requires_broad_redesign": False, "requires_live_infra_touch": False,
     "validation_commands": ["make check"]},
    {"packet_id": "add-fallback-justification-model",
     "description": "Add typed fallback justification model",
     "file_scope_count": 3, "has_external_api_calls": False,
     "requires_broad_redesign": False, "requires_live_infra_touch": False,
     "validation_commands": ["make check", "pytest tests/test_ledt_fallback_justification_seam.py -v"]},
    {"packet_id": "broad-cloud-integration-disqualified",
     "description": "Hypothetical cloud integration (disqualified by external API calls)",
     "file_scope_count": 2, "has_external_api_calls": True,
     "requires_broad_redesign": False, "requires_live_infra_touch": False,
     "validation_commands": ["make check"]},
]

def main():
    harness = LocalFirstProofHarness()
    record = harness.run(SAMPLES)
    path = harness.emit(record, ARTIFACT_DIR)
    print(f"samples_total:     {record.samples_total}")
    print(f"local_route_count: {record.local_route_count}")
    print(f"local_first_rate:  {record.local_first_rate}")
    for r in record.sample_results:
        print(f"  {r.sample_id[:40]}: {r.route_chosen}")
    print(f"artifact:          {path}")

if __name__ == "__main__":
    main()
