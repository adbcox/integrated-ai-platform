"""Tests for APCC1-P2: permission gate wiring seam."""
import pytest

from framework.aider_permission_gate_provider import (
    BOUNDED_AIDER_GATE,
    BOUNDED_AIDER_TOOL_PERMISSION,
    make_wired_preflight_checker,
    check_permission_gate_active,
)
from framework.typed_permission_gate import TypedPermissionGate
from framework.aider_preflight import AiderPreflightChecker


def test_bounded_gate_is_typed_permission_gate():
    assert isinstance(BOUNDED_AIDER_GATE, TypedPermissionGate)


def test_bounded_permission_is_allow():
    from framework.typed_permission_gate import ToolPermission
    assert BOUNDED_AIDER_TOOL_PERMISSION == ToolPermission.ALLOW


def test_make_wired_returns_checker():
    c = make_wired_preflight_checker()
    assert isinstance(c, AiderPreflightChecker)


def test_check_permission_gate_active_returns_bool():
    result = check_permission_gate_active()
    assert isinstance(result, bool)


def test_check_permission_gate_active_returns_true():
    assert check_permission_gate_active() is True


def test_wired_checker_permission_gate_check_passes():
    c = make_wired_preflight_checker()
    result = c.run_preflight()
    gate_check = next(ch for ch in result.checks if ch.check_name == "permission_gate_active")
    assert gate_check.passed is True


def test_wired_checker_preflight_result_has_checks():
    c = make_wired_preflight_checker()
    result = c.run_preflight()
    assert len(result.checks) > 0


def test_make_wired_creates_fresh_instance_each_call():
    c1 = make_wired_preflight_checker()
    c2 = make_wired_preflight_checker()
    assert c1 is not c2


def test_inspection_gate_passes_at_import():
    import framework.aider_permission_gate_provider  # noqa: F401 — verifies no AssertionError at import


def test_gate_sig_captured():
    import framework.aider_permission_gate_provider as m
    assert m._TPG_SIG and len(m._TPG_SIG) > 0
    assert m._APC_SIG and len(m._APC_SIG) > 0
