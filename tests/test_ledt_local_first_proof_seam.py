"""Seam tests for LEDT-P10-LOCAL-FIRST-PROOF-HARNESS-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.local_first_proof_harness import LocalFirstProofHarness, LocalFirstProofRecord, ProofSampleResult

BOUNDED = {"packet_id": "t1", "description": "add seam test", "file_scope_count": 2,
           "has_external_api_calls": False, "requires_broad_redesign": False,
           "requires_live_infra_touch": False, "validation_commands": ["make check"]}

def test_import_harness():
    assert callable(LocalFirstProofHarness)

def test_run_returns_record():
    r = LocalFirstProofHarness().run([BOUNDED])
    assert isinstance(r, LocalFirstProofRecord)

def test_bounded_sample_is_local():
    r = LocalFirstProofHarness().run([BOUNDED])
    assert r.sample_results[0].route_chosen == "local_execute"
    assert r.sample_results[0].is_local is True

def test_five_samples_correct_count():
    samples = [dict(BOUNDED, packet_id=f"s{i}") for i in range(5)]
    r = LocalFirstProofHarness().run(samples)
    assert r.samples_total == 5

def test_local_first_rate_high():
    samples = [dict(BOUNDED, packet_id=f"p{i}") for i in range(4)]
    samples.append({"packet_id": "ext", "description": "ext api", "file_scope_count": 2,
                    "has_external_api_calls": True, "requires_broad_redesign": False,
                    "requires_live_infra_touch": False, "validation_commands": ["make check"]})
    r = LocalFirstProofHarness().run(samples)
    assert r.local_first_rate >= 0.8

def test_emit_artifact(tmp_path):
    samples = [dict(BOUNDED, packet_id=f"p{i}") for i in range(5)]
    harness = LocalFirstProofHarness()
    record = harness.run(samples)
    path = harness.emit(record, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["samples_total"] == 5
    assert d["local_first_rate"] >= 0.8
    assert all(r["packet_description"] for r in d["sample_results"])
