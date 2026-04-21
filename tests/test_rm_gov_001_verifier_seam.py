"""Seam tests for RM-GOV-001 evidence verifier (RM-GOV-001-EVIDENCE-VERIFIER-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT = REPO_ROOT / "artifacts" / "rm_gov_verification" / "rm_gov_001_evidence.json"
EXPECTED_SUBCLAIMS = {
    "roadmap_to_development_tracking",
    "cmdb_linkage",
    "standardized_metrics",
    "enforced_naming",
    "impact_transparency",
}


def _load():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_import_verifier():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_rm_gov_001_verifier",
        REPO_ROOT / "bin" / "run_rm_gov_001_verifier.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.run)


def test_artifact_written():
    assert ARTIFACT.exists()


def test_artifact_parseable():
    d = _load()
    assert isinstance(d, dict)


def test_five_subclaims_present():
    d = _load()
    assert set(d["subclaims"].keys()) == EXPECTED_SUBCLAIMS


def test_each_subclaim_has_evidenced_bool():
    d = _load()
    for name, sub in d["subclaims"].items():
        assert isinstance(sub["evidenced"], bool), f"{name}.evidenced must be bool"


def test_evidenced_count_consistent():
    d = _load()
    actual = sum(1 for v in d["subclaims"].values() if v["evidenced"])
    assert d["evidenced_count"] == actual


def test_provisional_verdict_valid():
    d = _load()
    assert d["provisional_verdict"] in ("complete", "partial", "deferred")


def test_cmdb_linkage_evidenced():
    d = _load()
    assert d["subclaims"]["cmdb_linkage"]["evidenced"] is True, (
        "CMDB linkage must be evidenced; framework CMDB modules landed in prior campaign"
    )
