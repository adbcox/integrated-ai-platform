"""Tests for APCC1-P1: Aider preflight blocker inspector seam."""
import json
import pytest

from framework.aider_preflight_blocker_inspector import (
    inspect_preflight_blockers,
    PreflightBlockerArtifact,
    PreflightBlockerRecord,
    BLOCKER_PERMISSION_GATE,
    BLOCKER_CONFIG_KEYS,
)


def _artifact(dry_run=True):
    return inspect_preflight_blockers(dry_run=dry_run)


def test_returns_artifact():
    a = _artifact()
    assert isinstance(a, PreflightBlockerArtifact)


def test_total_blockers_is_two():
    a = _artifact()
    assert a.total_blockers == 2


def test_injectable_blockers_is_two():
    a = _artifact()
    assert a.injectable_blockers == 2


def test_non_injectable_blockers_is_zero():
    a = _artifact()
    assert a.non_injectable_blockers == 0


def test_blocker_names_present():
    a = _artifact()
    names = {r.blocker_name for r in a.blocker_records}
    assert BLOCKER_PERMISSION_GATE in names
    assert BLOCKER_CONFIG_KEYS in names


def test_records_are_preflight_blocker_records():
    a = _artifact()
    for r in a.blocker_records:
        assert isinstance(r, PreflightBlockerRecord)


def test_preflight_checker_constructor_nonempty():
    a = _artifact()
    assert a.preflight_checker_constructor and len(a.preflight_checker_constructor) > 0


def test_runtime_adapter_constructor_nonempty():
    a = _artifact()
    assert a.runtime_adapter_constructor and len(a.runtime_adapter_constructor) > 0


def test_permission_gate_interface_nonempty():
    a = _artifact()
    assert a.permission_gate_interface and len(a.permission_gate_interface) > 0


def test_config_surface_interface_nonempty():
    a = _artifact()
    assert a.config_surface_interface and len(a.config_surface_interface) > 0


def test_to_dict_schema_version():
    a = _artifact()
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_json_roundtrip():
    a = _artifact()
    d = a.to_dict()
    raw = json.dumps(d)
    loaded = json.loads(raw)
    assert loaded["schema_version"] == 1
    assert loaded["total_blockers"] == 2


def test_injection_paths_are_nonempty():
    a = _artifact()
    for r in a.blocker_records:
        assert r.injection_path and r.injection_path != "NO_INJECTABLE_PATH"


def test_bin_script_importable():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "run_aider_preflight_blocker_inspector",
        Path(__file__).resolve().parents[1] / "bin" / "run_aider_preflight_blocker_inspector.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_bin_script_dry_run_exits_zero(monkeypatch, capsys):
    import sys
    from pathlib import Path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_aider_preflight_blocker_inspector",
        Path(__file__).resolve().parents[1] / "bin" / "run_aider_preflight_blocker_inspector.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["run_aider_preflight_blocker_inspector.py", "--dry-run"])
    result = mod.main()
    assert result == 0
