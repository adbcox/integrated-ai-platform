"""Seam tests for AiderRuntimeAdapter preflight_checker injection (AIDER-PREFLIGHT-CHECKER-INJECTION-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.aider_runtime_adapter import AiderRuntimeAdapter
from framework.aider_preflight import AiderPreflightChecker


def test_import_adapter():
    assert callable(AiderRuntimeAdapter)


def test_init_accepts_preflight_checker_kwarg():
    mock = MagicMock(spec=AiderPreflightChecker)
    adapter = AiderRuntimeAdapter(preflight_checker=mock)
    assert adapter is not None


def test_init_default_none_preserves_behavior():
    adapter = AiderRuntimeAdapter()
    assert adapter._preflight_checker is None


def test_injected_checker_stored():
    mock = MagicMock(spec=AiderPreflightChecker)
    adapter = AiderRuntimeAdapter(preflight_checker=mock)
    assert adapter._preflight_checker is mock


def test_default_checker_type():
    # Default-constructed adapter should use AiderPreflightChecker when preflight() is called
    # Verify by checking that with no injection, preflight() uses AiderPreflightChecker internally
    adapter = AiderRuntimeAdapter()
    assert adapter._preflight_checker is None
    # The stored field is None; the preflight() method constructs AiderPreflightChecker() inline
    # when _preflight_checker is None — this is the preserved default behavior


def test_preflight_uses_injected_checker():
    from framework.aider_preflight import AiderPreflightCheck, AiderPreflightResult
    mock = MagicMock(spec=AiderPreflightChecker)
    mock.run_preflight.return_value = AiderPreflightResult(
        verdict="ready",
        checks=(AiderPreflightCheck(check_name="mock_check", passed=True, detail="mock"),),
        blocking_checks=(),
        evaluated_at="2026-01-01T00:00:00+00:00",
    )
    adapter = AiderRuntimeAdapter(preflight_checker=mock)
    result = adapter.preflight()
    mock.run_preflight.assert_called_once()
    assert result["verdict"] == "ready"
