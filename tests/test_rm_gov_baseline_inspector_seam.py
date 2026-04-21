"""Seam tests for RM-GOV baseline inspector (RM-GOV-BASELINE-INSPECTOR-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _load_artifact():
    p = REPO_ROOT / "artifacts" / "rm_gov_verification" / "baseline.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_import_baseline_inspector():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_rm_gov_baseline_inspector",
        REPO_ROOT / "bin" / "run_rm_gov_baseline_inspector.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.run)


def test_governance_canonical_roadmap_inspected():
    d = _load_artifact()
    assert "canonical_roadmap.json" in d["governance_files"]
    assert "present" in d["governance_files"]["canonical_roadmap.json"]


def test_baseline_artifact_written():
    p = REPO_ROOT / "artifacts" / "rm_gov_verification" / "baseline.json"
    assert p.exists()


def test_baseline_artifact_parseable():
    d = _load_artifact()
    assert isinstance(d, dict)


def test_rm_gov_entries_recorded():
    d = _load_artifact()
    assert "rm_gov_001_raw_entry" in d
    assert "rm_gov_002_raw_entry" in d
    assert "rm_gov_003_raw_entry" in d


def test_baseline_gaps_is_list():
    d = _load_artifact()
    assert isinstance(d["baseline_gaps"], list)
