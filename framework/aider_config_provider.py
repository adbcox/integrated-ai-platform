"""APCC1-P3: Bounded Aider config surface completing all blocking preflight checks."""
from __future__ import annotations

import inspect as _inspect

# --- Inspection gate ---
from framework.aider_preflight import AiderPreflightChecker as _APC

_APC_SIG = str(_inspect.signature(_APC.__init__))
assert "config" in _APC_SIG, (
    f"INTERFACE MISMATCH: AiderPreflightChecker has no config kwarg — sig={_APC_SIG}"
)

# Confirm config surface: plain dict, required keys {"model", "edit_format"}
# (verified by reading AiderPreflightChecker.run_preflight source)
_REQUIRED_CONFIG_KEYS = {"model", "edit_format"}

# --- Providers ---

from framework.aider_permission_gate_provider import BOUNDED_AIDER_GATE as _BOUNDED_GATE

BOUNDED_AIDER_CONFIG: dict = {
    "model": "gpt-4o",
    "edit_format": "diff",
}


def make_fully_wired_preflight_checker() -> _APC:
    return _APC(gate=_BOUNDED_GATE, config=BOUNDED_AIDER_CONFIG)


def check_config_keys_present() -> bool:
    checker = make_fully_wired_preflight_checker()
    result = checker.run_preflight()
    for c in result.checks:
        if c.check_name == "config_keys_present":
            return c.passed
    return False


def check_all_blocking_checks_pass() -> bool:
    checker = make_fully_wired_preflight_checker()
    result = checker.run_preflight()
    blocking_names = {"aider_importable", "permission_gate_active", "config_keys_present"}
    for c in result.checks:
        if c.check_name in blocking_names and not c.passed:
            return False
    return True
