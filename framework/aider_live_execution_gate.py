"""AiderLiveExecutionGate — LAPC1 P2.

Evaluates four checks to determine if live Aider execution is safe in this environment.
Inspection gate confirmed:
  KNOWN_FRAMEWORK_COMMANDS: ['check', 'quick', 'test_offline']
  AiderPreflightResult fields: verdict, checks, blocking_checks, evaluated_at, artifact_path
  AiderPreflightChecker.run_preflight: (self) -> AiderPreflightResult
  DEFAULT_AIDER_POLICY.ollama_first: True
  DEFAULT_AIDER_POLICY.dry_run_default: True
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.local_command_runner import LocalCommandRunner as _LocalCommandRunner, KNOWN_FRAMEWORK_COMMANDS as _KNOWN_FRAMEWORK_COMMANDS
from framework.aider_preflight import AiderPreflightChecker as _AiderPreflightChecker, AiderPreflightResult as _AiderPreflightResult
from framework.aider_adapter_contract import DEFAULT_AIDER_POLICY as _DEFAULT_AIDER_POLICY

assert hasattr(_AiderPreflightChecker, "run_preflight"), "INTERFACE MISMATCH: AiderPreflightChecker.run_preflight"
assert "verdict" in _AiderPreflightResult.__dataclass_fields__, "INTERFACE MISMATCH: AiderPreflightResult.verdict"
assert "blocking_checks" in _AiderPreflightResult.__dataclass_fields__, "INTERFACE MISMATCH: AiderPreflightResult.blocking_checks"
assert hasattr(_DEFAULT_AIDER_POLICY, "ollama_first"), "INTERFACE MISMATCH: DEFAULT_AIDER_POLICY.ollama_first"
assert hasattr(_DEFAULT_AIDER_POLICY, "dry_run_default"), "INTERFACE MISMATCH: DEFAULT_AIDER_POLICY.dry_run_default"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "aider_live_gate"

LIVE_GATE_PASS = "live_gate_pass"
LIVE_GATE_BLOCK = "live_gate_block"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AiderLiveGateCheck:
    check_name: str
    passed: bool
    observed_value: str
    required_value: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "observed_value": self.observed_value,
            "required_value": self.required_value,
            "detail": self.detail,
        }


@dataclass
class AiderLiveGateReport:
    checks: list
    overall_result: str
    live_execution_safe: bool
    blocking_checks: list
    generated_at: str
    artifact_path: str = ""

    @property
    def passed(self) -> bool:
        return self.overall_result == LIVE_GATE_PASS

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "overall_result": self.overall_result,
            "live_execution_safe": self.live_execution_safe,
            "blocking_checks": list(self.blocking_checks),
            "generated_at": self.generated_at,
            "checks": [c.to_dict() for c in self.checks],
        }


def evaluate_aider_live_gate(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> AiderLiveGateReport:
    # Check 1: command_registered
    aider_registered = "aider" in _KNOWN_FRAMEWORK_COMMANDS
    check_command = AiderLiveGateCheck(
        check_name="command_registered",
        passed=aider_registered,
        observed_value=str(sorted(_KNOWN_FRAMEWORK_COMMANDS)),
        required_value="'aider' in KNOWN_FRAMEWORK_COMMANDS",
        detail="'aider' must be registered before live execution is safe",
    )

    # Check 2: preflight_verdict
    try:
        preflight_result = _AiderPreflightChecker().run_preflight()
        preflight_verdict = preflight_result.verdict
        preflight_pass = (preflight_verdict == "pass")
    except Exception as exc:
        preflight_verdict = f"exception: {exc}"
        preflight_pass = False

    check_preflight = AiderLiveGateCheck(
        check_name="preflight_verdict",
        passed=preflight_pass,
        observed_value=str(preflight_verdict),
        required_value="pass",
        detail="AiderPreflightChecker must report 'pass' for live execution to be safe",
    )

    # Check 3: policy_ollama_first
    ollama_first = _DEFAULT_AIDER_POLICY.ollama_first
    check_policy = AiderLiveGateCheck(
        check_name="policy_ollama_first",
        passed=bool(ollama_first),
        observed_value=str(ollama_first),
        required_value="True",
        detail="Ollama-first policy must be active for local-first safe execution",
    )

    # Check 4: dry_run_default_safe
    dry_run_default = _DEFAULT_AIDER_POLICY.dry_run_default
    check_dry_run = AiderLiveGateCheck(
        check_name="dry_run_default_safe",
        passed=bool(dry_run_default),
        observed_value=str(dry_run_default),
        required_value="True",
        detail="dry_run_default must be True to prevent accidental live runs",
    )

    checks = [check_command, check_preflight, check_policy, check_dry_run]
    live_execution_safe = all(c.passed for c in checks)
    overall_result = LIVE_GATE_PASS if live_execution_safe else LIVE_GATE_BLOCK
    blocking_checks = [c.check_name for c in checks if not c.passed]

    report = AiderLiveGateReport(
        checks=checks,
        overall_result=overall_result,
        live_execution_safe=live_execution_safe,
        blocking_checks=blocking_checks,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_aider_live_gate.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "LIVE_GATE_PASS",
    "LIVE_GATE_BLOCK",
    "AiderLiveGateCheck",
    "AiderLiveGateReport",
    "evaluate_aider_live_gate",
]
