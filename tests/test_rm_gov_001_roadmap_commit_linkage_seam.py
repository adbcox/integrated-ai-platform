"""Seam tests for RM-GOV-001-ROADMAP-COMMIT-LINKAGE-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bin.run_rm_gov_001_roadmap_commit_linkage import (
    _read_last_execution_commit,
    emit_linkage,
    run_linkage,
    verify_tracking_subclaim_flips,
)

_YAML_DIR = REPO_ROOT / "docs" / "roadmap" / "items"


def test_import_linkage():
    from bin.run_rm_gov_001_roadmap_commit_linkage import run_linkage
    assert callable(run_linkage)


def test_all_populated():
    result = run_linkage()
    assert result["all_populated"] is True


def test_rm_gov_001_yaml_has_commit():
    sha = _read_last_execution_commit(_YAML_DIR / "RM-GOV-001.yaml")
    assert sha is not None and len(sha) >= 7


def test_rm_gov_002_yaml_has_commit():
    sha = _read_last_execution_commit(_YAML_DIR / "RM-GOV-002.yaml")
    assert sha is not None and len(sha) >= 7


def test_rm_gov_003_yaml_has_commit():
    sha = _read_last_execution_commit(_YAML_DIR / "RM-GOV-003.yaml")
    assert sha is not None and len(sha) >= 7


def test_tracking_subclaim_flipped():
    flip = verify_tracking_subclaim_flips()
    assert flip["evidenced"] is True, (
        f"roadmap_to_development_tracking still false: {flip['evidence_detail']}"
    )
