"""Conformance tests for framework/aider_preflight.py (ADSC1-AIDER-PREFLIGHT-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.aider_preflight import (
    AiderPreflightCheck,
    AiderPreflightChecker,
    AiderPreflightResult,
    emit_preflight_artifact,
)
from framework.typed_permission_gate import ToolPermission, TypedPermissionGate


def _gate():
    return TypedPermissionGate(default_permission=ToolPermission.ALLOW)


def _full_config():
    return {"model": "gpt-4", "edit_format": "diff"}


# --- import ---

def test_import_aider_preflight_checker():
    assert callable(AiderPreflightChecker)


def test_returns_result_type():
    r = AiderPreflightChecker().run_preflight()
    assert isinstance(r, AiderPreflightResult)


# --- verdict values ---

def test_verdict_is_valid_string():
    r = AiderPreflightChecker().run_preflight()
    assert r.verdict in {"ready", "not_ready", "unknown"}


def test_not_ready_without_gate():
    r = AiderPreflightChecker(gate=None, config=_full_config()).run_preflight()
    blocking = {c.check_name: c for c in r.blocking_checks}
    assert not blocking["permission_gate_active"].passed


def test_not_ready_missing_config_model():
    r = AiderPreflightChecker(gate=_gate(), config={"edit_format": "diff"}).run_preflight()
    blocking = {c.check_name: c for c in r.blocking_checks}
    assert not blocking["config_keys_present"].passed


def test_not_ready_missing_config_edit_format():
    r = AiderPreflightChecker(gate=_gate(), config={"model": "x"}).run_preflight()
    blocking = {c.check_name: c for c in r.blocking_checks}
    assert not blocking["config_keys_present"].passed


# --- blocking vs advisory ---

def test_blocking_checks_names():
    r = AiderPreflightChecker().run_preflight()
    names = {c.check_name for c in r.blocking_checks}
    assert {"aider_importable", "permission_gate_active", "config_keys_present"} == names


def test_advisory_check_present():
    r = AiderPreflightChecker().run_preflight()
    names = {c.check_name for c in r.checks}
    assert "aider_version_detectable" in names
    assert "working_tree_clean" in names


# --- run_preflight does not raise ---

def test_run_preflight_no_exception():
    r = AiderPreflightChecker().run_preflight()
    assert r is not None


def test_not_ready_is_valid_outcome():
    r = AiderPreflightChecker(gate=None).run_preflight()
    assert r.verdict in {"not_ready", "unknown"}


# --- AiderPreflightCheck fields ---

def test_check_fields_present():
    c = AiderPreflightCheck(check_name="x", passed=True, detail="ok")
    assert c.check_name == "x"
    assert c.passed is True
    assert c.detail == "ok"


# --- artifact emission ---

def test_artifact_written(tmp_path):
    r = AiderPreflightChecker().run_preflight()
    path = emit_preflight_artifact(r, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable_json(tmp_path):
    r = AiderPreflightChecker().run_preflight()
    path = emit_preflight_artifact(r, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "verdict" in data
    assert "checks" in data


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "AiderPreflightChecker")
    assert hasattr(framework, "AiderPreflightResult")
    assert hasattr(framework, "AiderPreflightCheck")
    assert hasattr(framework, "emit_preflight_artifact")
