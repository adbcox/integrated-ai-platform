"""Tests for APCC1-P3: config key completion seam."""
import pytest

from framework.aider_config_provider import (
    BOUNDED_AIDER_CONFIG,
    make_fully_wired_preflight_checker,
    check_config_keys_present,
    check_all_blocking_checks_pass,
)
from framework.aider_preflight import AiderPreflightChecker


def test_bounded_config_has_model():
    assert "model" in BOUNDED_AIDER_CONFIG


def test_bounded_config_has_edit_format():
    assert "edit_format" in BOUNDED_AIDER_CONFIG


def test_bounded_config_values_nonempty():
    assert BOUNDED_AIDER_CONFIG["model"]
    assert BOUNDED_AIDER_CONFIG["edit_format"]


def test_make_fully_wired_returns_checker():
    c = make_fully_wired_preflight_checker()
    assert isinstance(c, AiderPreflightChecker)


def test_check_config_keys_present_returns_bool():
    result = check_config_keys_present()
    assert isinstance(result, bool)


def test_check_config_keys_present_returns_true():
    assert check_config_keys_present() is True


def test_check_all_blocking_checks_pass_returns_bool():
    result = check_all_blocking_checks_pass()
    assert isinstance(result, bool)


def test_check_all_blocking_checks_pass_returns_true():
    assert check_all_blocking_checks_pass() is True


def test_wired_checker_no_blocking_failures():
    c = make_fully_wired_preflight_checker()
    result = c.run_preflight()
    blocking_names = {"aider_importable", "permission_gate_active", "config_keys_present"}
    for ch in result.checks:
        if ch.check_name in blocking_names:
            assert ch.passed, f"Blocking check failed: {ch.check_name} — {ch.detail}"


def test_inspection_gate_passes_at_import():
    import framework.aider_config_provider  # noqa: F401 — verifies no AssertionError at import
