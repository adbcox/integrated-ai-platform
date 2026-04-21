"""Seam tests for CMDB authority contract (CMDB-AUTHORITY-CONTRACT-SEAM-1)."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_authority_contract import (
    CmdbServiceRecord,
    CmdbOwnershipBoundary,
    CmdbAuthorityContract,
    build_cmdb_authority_contract,
    emit_cmdb_authority_contract,
)


def test_import_contract():
    assert callable(build_cmdb_authority_contract)


def test_build_returns_contract():
    c = build_cmdb_authority_contract()
    assert isinstance(c, CmdbAuthorityContract)


def test_contract_version_set():
    c = build_cmdb_authority_contract()
    assert c.contract_version == "1.0"


def test_authority_domain_is_service_inventory():
    c = build_cmdb_authority_contract()
    assert c.authority_domain == "service_inventory"


def test_service_record_fields():
    r = CmdbServiceRecord(
        service_name="svc", subsystem="sub", owner="team",
        adapter_status="active", runtime_binding="worker_runtime"
    )
    assert r.service_name == "svc"
    assert r.adapter_status == "active"
    assert r.runtime_binding == "worker_runtime"


def test_ownership_boundary_fields():
    b = CmdbOwnershipBoundary(
        boundary_name="svc_boundary", owned_by="cmdb",
        resource_types=["service_records"], non_overlapping_with=["promotion_manifest"]
    )
    assert b.boundary_name == "svc_boundary"
    assert b.owned_by == "cmdb"


def test_contract_with_service_records():
    r = CmdbServiceRecord(service_name="x", subsystem="y", owner="z", adapter_status="active", runtime_binding=None)
    c = build_cmdb_authority_contract(service_records=(r,))
    assert len(c.service_records) == 1
    assert c.service_records[0].service_name == "x"


def test_owned_resource_types_from_cmdb_authority():
    from framework.cmdb_authority_boundary import CMDB_AUTHORITY
    c = build_cmdb_authority_contract()
    assert set(c.owned_resource_types) == set(CMDB_AUTHORITY.owns)


def test_contract_service_records_is_tuple():
    c = build_cmdb_authority_contract()
    assert isinstance(c.service_records, tuple)


def test_emit_artifact_written(tmp_path):
    c = build_cmdb_authority_contract()
    path = emit_cmdb_authority_contract(c, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    c = build_cmdb_authority_contract()
    path = emit_cmdb_authority_contract(c, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "contract_version" in data
    assert "authority_domain" in data
    assert data["authority_domain"] == "service_inventory"


def test_emit_artifact_path_set(tmp_path):
    c = build_cmdb_authority_contract()
    path = emit_cmdb_authority_contract(c, artifact_dir=tmp_path)
    assert Path(path).name == "authority_contract.json"


def test_contract_frozen_immutable():
    c = build_cmdb_authority_contract()
    try:
        c.contract_version = "2.0"
        assert False, "should have raised FrozenInstanceError"
    except dataclasses.FrozenInstanceError:
        pass


def test_package_surface():
    import framework
    assert hasattr(framework, "CmdbAuthorityContract")
    assert hasattr(framework, "CmdbServiceRecord")
    assert hasattr(framework, "build_cmdb_authority_contract")
