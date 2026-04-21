"""Emit live_gate_proof artifact for post-injection wired preflight checker path."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.aider_runtime_adapter import AiderRuntimeAdapter
from framework.aider_preflight import AiderPreflightCheck, AiderPreflightResult, AiderPreflightChecker


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_proof() -> dict:
    spy = MagicMock(spec=AiderPreflightChecker)
    spy.run_preflight.return_value = AiderPreflightResult(
        verdict="ready",
        checks=(AiderPreflightCheck(check_name="injected_check", passed=True, detail="injected"),),
        blocking_checks=(),
        evaluated_at=_iso_now(),
    )

    adapter = AiderRuntimeAdapter(preflight_checker=spy)
    subprocess_called = False

    original_run = subprocess.run

    def _interceptor(*args, **kwargs):
        nonlocal subprocess_called
        subprocess_called = True
        return original_run(*args, **kwargs)

    with patch("subprocess.run", side_effect=_interceptor):
        result = adapter.preflight()

    wired_checker_called = spy.run_preflight.call_count == 1
    propagation_verified = result.get("verdict") == "ready"
    subprocess_isolation_verified = not subprocess_called

    gate_passed = wired_checker_called and propagation_verified and subprocess_isolation_verified
    blocking_reason = None
    if not wired_checker_called:
        blocking_reason = "injected checker was not called by adapter.preflight()"
    elif not propagation_verified:
        blocking_reason = f"verdict not propagated: got {result.get('verdict')!r}"
    elif not subprocess_isolation_verified:
        blocking_reason = "subprocess.run was called despite injected checker being present"

    return {
        "gate_passed": gate_passed,
        "wired_checker_called": wired_checker_called,
        "propagation_verified": propagation_verified,
        "subprocess_isolation_verified": subprocess_isolation_verified,
        "proven_at": _iso_now(),
        "blocking_reason": blocking_reason,
    }


def main() -> int:
    proof = run_proof()
    artifact_dir = REPO_ROOT / "artifacts" / "aider_preflight_injection"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "live_gate_proof.json"
    out_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")

    print(f"\n{'='*55}")
    print("  Aider Post-Injection Live Gate Proof")
    print(f"{'='*55}")
    print(f"  gate_passed                : {proof['gate_passed']}")
    print(f"  wired_checker_called       : {proof['wired_checker_called']}")
    print(f"  propagation_verified       : {proof['propagation_verified']}")
    print(f"  subprocess_isolation_verified: {proof['subprocess_isolation_verified']}")
    if proof["blocking_reason"]:
        print(f"  blocking_reason            : {proof['blocking_reason']}")
    print(f"  artifact                   : {out_path}")
    print(f"{'='*55}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
