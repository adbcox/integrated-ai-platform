"""Tests for framework.cmdb_authority_pilot — CMDB authority pilot seam."""
import pytest
from pathlib import Path

from framework.cmdb_authority_pilot import CmdbAuthorityRecord, CmdbAuthorityPilot, read_cmdb_authority


def test_import_ok():
    from framework.cmdb_authority_pilot import CmdbAuthorityPilot, CmdbAuthorityRecord  # noqa: F401


def test_read_authority_returns_record():
    rec = CmdbAuthorityPilot().read_authority()
    assert isinstance(rec, CmdbAuthorityRecord)


def test_current_phase_non_empty():
    rec = CmdbAuthorityPilot().read_authority()
    assert rec.current_phase != ""


def test_read_at_is_iso():
    rec = CmdbAuthorityPilot().read_authority()
    assert "T" in rec.read_at


def test_gates_summary_is_dict():
    rec = CmdbAuthorityPilot().read_authority()
    assert isinstance(rec.gates_summary, dict)


def test_next_package_class_non_empty():
    rec = CmdbAuthorityPilot().read_authority()
    assert rec.next_package_class != ""


def test_contract_version_non_empty():
    rec = CmdbAuthorityPilot().read_authority()
    assert rec.contract_version != ""


def test_phases_count_is_int():
    rec = CmdbAuthorityPilot().read_authority()
    assert isinstance(rec.phases_count, int)
    assert rec.phases_count >= 0


def test_record_is_frozen():
    rec = CmdbAuthorityPilot().read_authority()
    with pytest.raises((AttributeError, TypeError)):
        rec.current_phase = "modified"  # type: ignore


def test_read_cmdb_authority_convenience():
    rec = read_cmdb_authority()
    assert isinstance(rec, CmdbAuthorityRecord)


def test_missing_current_phase_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        CmdbAuthorityPilot(governance_dir=tmp_path).read_authority()


def test_optional_files_default_safely(tmp_path):
    # Only current_phase.json present
    cp = tmp_path / "current_phase.json"
    cp.write_text('{"current_phase_id": "test", "current_phase_status": "open"}')
    rec = CmdbAuthorityPilot(governance_dir=tmp_path).read_authority()
    assert rec.current_phase == "test"
    assert rec.gates_summary == {}
    assert rec.phases_count == 0
    assert rec.contract_version == "unknown"


def test_init_ok_from_framework():
    from framework import read_cmdb_authority  # noqa: F401


def test_fields_list():
    rec = CmdbAuthorityPilot().read_authority()
    expected_fields = {
        "current_phase", "current_phase_status", "next_package_class",
        "contract_version", "gates_summary", "phases_count", "read_at"
    }
    actual_fields = set(rec.__dataclass_fields__.keys())
    assert expected_fields == actual_fields
