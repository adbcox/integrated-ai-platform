"""CodexAvailabilityGate — LAPC1 P5.

Inspects Codex availability and policy gate state. No SDK imports, no subprocess.
Inspection gate confirmed:
  DEFAULT_CODEX_POLICY fields: optional, allow_without_api_key, require_explicit_authorization,
                                dry_run_default, max_context_files
  DEFAULT_CODEX_POLICY.optional: True
  DEFAULT_CODEX_POLICY.allow_without_api_key: False
  CodexAdapterConfig.is_defer_candidate: (self) -> bool
  CODEX_AVAILABLE: False (no env key)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.codex_adapter_contract import (
    DEFAULT_CODEX_POLICY as _DEFAULT_CODEX_POLICY,
    CodexAdapterConfig as _CodexAdapterConfig,
    CodexAdapterPolicy as _CodexAdapterPolicy,
)
from framework.codex_defer_adapter import CODEX_AVAILABLE as _CODEX_AVAILABLE

assert "optional" in _DEFAULT_CODEX_POLICY.__dataclass_fields__, "INTERFACE MISMATCH: DEFAULT_CODEX_POLICY.optional"
assert "allow_without_api_key" in _DEFAULT_CODEX_POLICY.__dataclass_fields__, "INTERFACE MISMATCH: DEFAULT_CODEX_POLICY.allow_without_api_key"
assert hasattr(_CodexAdapterConfig, "is_defer_candidate"), "INTERFACE MISMATCH: CodexAdapterConfig.is_defer_candidate"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "codex_availability"

CODEX_GATE_PASS = "codex_gate_pass"
CODEX_GATE_BLOCK = "codex_gate_block"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CodexAvailabilityCheck:
    check_name: str
    passed: bool
    observed_value: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "observed_value": self.observed_value,
            "detail": self.detail,
        }


@dataclass
class CodexAvailabilityReport:
    checks: list
    overall_result: str
    codex_available: bool
    policy_allows_execution: bool
    blocking_reason: str
    generated_at: str
    artifact_path: str = ""

    @property
    def passed(self) -> bool:
        return self.overall_result == CODEX_GATE_PASS

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "overall_result": self.overall_result,
            "codex_available": self.codex_available,
            "policy_allows_execution": self.policy_allows_execution,
            "blocking_reason": self.blocking_reason,
            "generated_at": self.generated_at,
            "checks": [c.to_dict() for c in self.checks],
        }


def evaluate_codex_availability(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> CodexAvailabilityReport:
    # Check 1: env_key_present
    env_key_present = bool(_CODEX_AVAILABLE)
    check_env = CodexAvailabilityCheck(
        check_name="env_key_present",
        passed=env_key_present,
        observed_value=str(env_key_present),
        detail="ANTHROPIC_API_KEY or OPENAI_API_KEY must be set for Codex execution",
    )

    # Check 2: policy_optional
    policy_optional = bool(_DEFAULT_CODEX_POLICY.optional)
    check_optional = CodexAvailabilityCheck(
        check_name="policy_optional",
        passed=policy_optional,
        observed_value=str(policy_optional),
        detail="Policy marks Codex as optional; non-optional policy would hard-block other surfaces",
    )

    # Check 3: policy_allows_without_key
    allows_without_key = bool(_DEFAULT_CODEX_POLICY.allow_without_api_key)
    check_allows_without_key = CodexAvailabilityCheck(
        check_name="policy_allows_without_key",
        passed=allows_without_key,
        observed_value=str(allows_without_key),
        detail="Policy allow_without_api_key=False means execution requires env key",
    )

    # Check 4: defer_candidate_when_no_key
    # Build minimal config to call is_defer_candidate
    test_config = _CodexAdapterConfig(
        model="",
        message="",
        target_files=[],
        policy=_DEFAULT_CODEX_POLICY,
    )
    is_defer = test_config.is_defer_candidate()
    check_defer = CodexAvailabilityCheck(
        check_name="defer_candidate_when_no_key",
        passed=is_defer,
        observed_value=str(is_defer),
        detail="When no env key, config must identify itself as defer candidate",
    )

    checks = [check_env, check_optional, check_allows_without_key, check_defer]

    # policy_allows_execution = env key present AND policy allows without key OR (env key present)
    # Realistically: only True if env_key_present
    policy_allows_execution = env_key_present and not is_defer
    codex_available = env_key_present

    if env_key_present and not is_defer:
        overall_result = CODEX_GATE_PASS
        blocking_reason = ""
    else:
        overall_result = CODEX_GATE_BLOCK
        reasons = []
        if not env_key_present:
            reasons.append("no ANTHROPIC_API_KEY or OPENAI_API_KEY in env")
        if is_defer:
            reasons.append("config is_defer_candidate=True")
        blocking_reason = "; ".join(reasons)

    report = CodexAvailabilityReport(
        checks=checks,
        overall_result=overall_result,
        codex_available=codex_available,
        policy_allows_execution=policy_allows_execution,
        blocking_reason=blocking_reason,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_codex_availability.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "CODEX_GATE_PASS",
    "CODEX_GATE_BLOCK",
    "CodexAvailabilityCheck",
    "CodexAvailabilityReport",
    "evaluate_codex_availability",
]
