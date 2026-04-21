"""Seam tests for CMDB read model (CMDB-READ-MODEL-COMPLETION-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_read_model import CmdbReadModel, CmdbReadModelEntry, CmdbReadModelOutput, emit_cmdb_read_model
from framework.cmdb_authority_contract import build_cmdb_authority_contract, CmdbServiceRecord


def test_import_read_model():
    assert callable(CmdbReadModel)


def test_build_returns_output():
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    assert isinstance(out, CmdbReadModelOutput)


def test_output_type():
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    assert hasattr(out, "read_model_complete")
    assert hasattr(out, "total_entries")


def test_entries_populated_from_contract():
    c = build_cmdb_authority_contract()
    out = CmdbReadModel().build(contract=c)
    assert out.total_entries == len(c.owned_resource_types)


def test_all_entries_readable():
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    assert out.readable_count == out.total_entries


def test_all_entries_stable():
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    assert out.stable_count == out.total_entries


def test_read_model_complete_when_all_readable():
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    assert out.read_model_complete is True


def test_read_model_incomplete_when_unknown_adapter():
    rec = CmdbServiceRecord(
        service_name="svc", subsystem="sub", owner="team",
        adapter_status="unknown", runtime_binding=None,
    )
    c = build_cmdb_authority_contract(service_records=(rec,))
    out = CmdbReadModel().build(contract=c)
    assert out.read_model_complete is False


def test_readable_count_accurate():
    rec = CmdbServiceRecord(
        service_name="svc", subsystem="sub", owner="team",
        adapter_status="active", runtime_binding=None,
    )
    c = build_cmdb_authority_contract(service_records=(rec,))
    out = CmdbReadModel().build(contract=c)
    assert out.readable_count == out.total_entries


def test_entry_is_frozen():
    import dataclasses
    e = CmdbReadModelEntry(entry_name="x", resource_type="r", readable=True, stable=True, detail="d")
    try:
        e.readable = False
        assert False, "should have raised"
    except dataclasses.FrozenInstanceError:
        pass


def test_emit_artifact_written(tmp_path):
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    path = emit_cmdb_read_model(out, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    out = CmdbReadModel().build(contract=build_cmdb_authority_contract())
    path = emit_cmdb_read_model(out, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "read_model_complete" in data
    assert "entries" in data


def test_package_surface():
    import framework
    assert hasattr(framework, "CmdbReadModel")
    assert hasattr(framework, "CmdbReadModelOutput")
