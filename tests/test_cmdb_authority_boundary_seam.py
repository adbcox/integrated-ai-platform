"""Seam tests for CMDB authority boundary (CMDB-AUTHORITY-BOUNDARY-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_authority_boundary import (
    AuthorityDomain,
    PROMOTION_AUTHORITY,
    RUNTIME_AUTHORITY,
    CMDB_AUTHORITY,
    ALL_AUTHORITIES,
    validate_boundary_non_overlap,
    emit_authority_boundary,
)


def test_import_authority_boundary():
    assert callable(validate_boundary_non_overlap)


def test_promotion_authority_exists():
    assert PROMOTION_AUTHORITY.domain_name == "promotion_release"


def test_runtime_authority_exists():
    assert RUNTIME_AUTHORITY.domain_name == "architecture_runtime"


def test_cmdb_authority_exists():
    assert CMDB_AUTHORITY.domain_name == "service_inventory"


def test_three_domains_defined():
    assert len(ALL_AUTHORITIES) == 3


def test_no_overlap_in_owns():
    assert validate_boundary_non_overlap() == []


def test_cmdb_does_not_own_promotion_artifacts():
    assert "promotion_manifest" not in CMDB_AUTHORITY.owns
    assert "release_gate" not in CMDB_AUTHORITY.owns


def test_promotion_does_not_own_service_inventory():
    assert "service_inventory" not in PROMOTION_AUTHORITY.owns
    assert "service_records" not in PROMOTION_AUTHORITY.owns


def test_cmdb_source_of_truth_path_is_none():
    assert CMDB_AUTHORITY.source_of_truth_path is None


def test_authority_domain_is_frozen():
    import dataclasses
    try:
        CMDB_AUTHORITY.domain_name = "other"
        assert False, "should have raised"
    except dataclasses.FrozenInstanceError:
        pass


def test_emit_artifact_written(tmp_path):
    path = emit_authority_boundary(artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    path = emit_authority_boundary(artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "domains" in data
    assert "overlap_violations" in data
    assert len(data["domains"]) == 3


def test_emit_artifact_overlap_violations_empty(tmp_path):
    path = emit_authority_boundary(artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert data["overlap_violations"] == []


def test_package_surface():
    import framework
    assert hasattr(framework, "AuthorityDomain")
    assert hasattr(framework, "CMDB_AUTHORITY")
    assert hasattr(framework, "validate_boundary_non_overlap")
