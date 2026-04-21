"""Seam tests for CMDB operating context (CMDB-OPERATING-CONTEXT-INTEGRATION-SEAM-1)."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_operating_context import (
    SubsystemEntry,
    HostSlot,
    CmdbOperatingContext,
    build_local_operating_context,
    emit_cmdb_operating_context,
)
from framework.cmdb_authority_contract import build_cmdb_authority_contract, CmdbServiceRecord


def test_import_operating_context():
    assert callable(build_local_operating_context)


def test_build_returns_context():
    ctx = build_local_operating_context(contract=build_cmdb_authority_contract())
    assert isinstance(ctx, CmdbOperatingContext)


def test_subsystem_entry_fields():
    s = SubsystemEntry(subsystem_name="s", runtime_adapter="r", adapter_active=True, owner="team")
    assert s.subsystem_name == "s"
    assert s.adapter_active is True


def test_host_slot_fields():
    h = HostSlot(slot_name="local_dev", environment="local", subsystems=("svc",))
    assert h.slot_name == "local_dev"
    assert h.environment == "local"


def test_empty_contract_produces_complete_context():
    ctx = build_local_operating_context(contract=build_cmdb_authority_contract())
    assert ctx.context_complete is True


def test_default_host_slot_environment_is_local():
    ctx = build_local_operating_context(contract=build_cmdb_authority_contract())
    assert len(ctx.host_slots) == 1
    assert ctx.host_slots[0].environment == "local"


def test_default_host_slot_name_is_local_dev():
    ctx = build_local_operating_context(contract=build_cmdb_authority_contract())
    assert ctx.host_slots[0].slot_name == "local_dev"


def test_context_with_service_records_mapped():
    rec = CmdbServiceRecord(
        service_name="svc1", subsystem="sub1", owner="teamA",
        adapter_status="active", runtime_binding="runtime_worker",
    )
    c = build_cmdb_authority_contract(service_records=(rec,))
    ctx = build_local_operating_context(contract=c)
    assert len(ctx.subsystems) == 1
    assert ctx.subsystems[0].subsystem_name == "sub1"
    assert ctx.subsystems[0].adapter_active is True


def test_context_complete_false_when_unknown_adapter():
    rec = CmdbServiceRecord(
        service_name="svc2", subsystem="sub2", owner="teamB",
        adapter_status="unknown", runtime_binding=None,
    )
    c = build_cmdb_authority_contract(service_records=(rec,))
    ctx = build_local_operating_context(contract=c)
    assert ctx.context_complete is False


def test_linked_contract_version_propagated():
    c = build_cmdb_authority_contract()
    ctx = build_local_operating_context(contract=c)
    assert ctx.linked_contract_version == c.contract_version


def test_emit_artifact_written(tmp_path):
    ctx = build_local_operating_context(contract=build_cmdb_authority_contract())
    path = emit_cmdb_operating_context(ctx, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    ctx = build_local_operating_context(contract=build_cmdb_authority_contract())
    path = emit_cmdb_operating_context(ctx, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "context_complete" in data
    assert "host_slots" in data
    assert "linked_contract_version" in data


def test_package_surface():
    import framework
    assert hasattr(framework, "CmdbOperatingContext")
    assert hasattr(framework, "build_local_operating_context")
