"""Seam tests for post-injection live gate and proof (AIDER-POST-INJECTION-LIVE-GATE-PROOF-1)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.aider_runtime_adapter import AiderRuntimeAdapter
from framework.aider_preflight import AiderPreflightCheck, AiderPreflightResult, AiderPreflightChecker


def _make_preflight_result(verdict="ready", blocking_checks=()):
    return AiderPreflightResult(
        verdict=verdict,
        checks=(AiderPreflightCheck(check_name="mock_check", passed=(verdict == "ready"), detail="mock"),),
        blocking_checks=blocking_checks,
        evaluated_at="2026-01-01T00:00:00+00:00",
    )


def test_wired_checker_called_on_preflight():
    spy = MagicMock(spec=AiderPreflightChecker)
    spy.run_preflight.return_value = _make_preflight_result("ready")
    adapter = AiderRuntimeAdapter(preflight_checker=spy)
    adapter.preflight()
    spy.run_preflight.assert_called_once()


def test_wired_checker_pass_result_propagates():
    spy = MagicMock(spec=AiderPreflightChecker)
    spy.run_preflight.return_value = _make_preflight_result("ready")
    adapter = AiderRuntimeAdapter(preflight_checker=spy)
    result = adapter.preflight()
    assert result["verdict"] == "ready"


def test_wired_checker_fail_result_propagates():
    spy = MagicMock(spec=AiderPreflightChecker)
    blocking = (AiderPreflightCheck(check_name="aider_importable", passed=False, detail="not found"),)
    spy.run_preflight.return_value = _make_preflight_result("not_ready", blocking_checks=blocking)
    adapter = AiderRuntimeAdapter(preflight_checker=spy)
    result = adapter.preflight()
    assert result["verdict"] == "not_ready"
    assert result["blocking_checks"] == 1


def test_no_subprocess_in_injection_path():
    spy = MagicMock(spec=AiderPreflightChecker)
    spy.run_preflight.return_value = _make_preflight_result("ready")
    adapter = AiderRuntimeAdapter(preflight_checker=spy)
    with patch("subprocess.run", side_effect=AssertionError("subprocess called unexpectedly")):
        result = adapter.preflight()
    assert result["verdict"] == "ready"


def test_proof_artifact_reflects_injection_success(tmp_path):
    spy = MagicMock(spec=AiderPreflightChecker)
    spy.run_preflight.return_value = _make_preflight_result("ready")
    adapter = AiderRuntimeAdapter(preflight_checker=spy)

    with patch("subprocess.run", side_effect=AssertionError("subprocess called")):
        result = adapter.preflight()

    wired_checker_called = spy.run_preflight.call_count == 1
    propagation_verified = result["verdict"] == "ready"
    subprocess_isolation_verified = True  # no exception from the patch means no subprocess called

    artifact = {
        "gate_passed": wired_checker_called and propagation_verified and subprocess_isolation_verified,
        "wired_checker_called": wired_checker_called,
        "propagation_verified": propagation_verified,
        "subprocess_isolation_verified": subprocess_isolation_verified,
        "proven_at": "2026-01-01T00:00:00+00:00",
        "blocking_reason": None,
    }
    out = tmp_path / "live_gate_proof.json"
    out.write_text(json.dumps(artifact, indent=2))
    data = json.loads(out.read_text())
    assert data["gate_passed"] is True
    assert data["wired_checker_called"] is True
