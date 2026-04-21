"""APCC1-P2: Minimal TypedPermissionGate factory for bounded Aider preflight."""
from __future__ import annotations

import inspect as _inspect

# --- Inspection gate (runs at import time) ---
from framework.typed_permission_gate import TypedPermissionGate as _TPG, ToolPermission as _TP
from framework.aider_preflight import AiderPreflightChecker as _APC

_TPG_SIG = str(_inspect.signature(_TPG.__init__))
_TP_SIG = str(_inspect.signature(_TP.__init__))
_APC_SIG = str(_inspect.signature(_APC.__init__))

assert "gate" in _APC_SIG, (
    f"INTERFACE MISMATCH: AiderPreflightChecker has no gate kwarg — sig={_APC_SIG}"
)

# --- Factories ---

BOUNDED_AIDER_TOOL_PERMISSION = _TP.ALLOW

BOUNDED_AIDER_GATE = _TPG(rules=[], default_permission=_TP.ALLOW)


def make_wired_preflight_checker() -> _APC:
    return _APC(gate=BOUNDED_AIDER_GATE)


def check_permission_gate_active() -> bool:
    checker = make_wired_preflight_checker()
    result = checker.run_preflight()
    for c in result.checks:
        if c.check_name == "permission_gate_active":
            return c.passed
    return False
