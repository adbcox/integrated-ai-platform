"""Aider controlled-adapter preflight checks. NOT an adapter implementation."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.typed_permission_gate import ToolPermission, TypedPermissionGate

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "aider_preflight"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AiderPreflightCheck:
    check_name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class AiderPreflightResult:
    verdict: str  # "ready", "not_ready", "unknown"
    checks: tuple
    blocking_checks: tuple
    evaluated_at: str
    artifact_path: Optional[str] = None


class AiderPreflightChecker:
    def __init__(
        self,
        *,
        gate: Optional[TypedPermissionGate] = None,
        config: Optional[dict] = None,
    ) -> None:
        self._gate = gate
        self._config = config or {}

    def run_preflight(self) -> AiderPreflightResult:
        checks = []
        unknown = False

        # Check 1 (blocking): aider_importable
        try:
            proc = subprocess.run(
                ["python3", "-c", "import aider"],
                capture_output=True,
                timeout=10,
            )
            aider_importable = proc.returncode == 0
            checks.append(AiderPreflightCheck(
                check_name="aider_importable",
                passed=aider_importable,
                detail="" if aider_importable else "aider not importable",
            ))
        except subprocess.TimeoutExpired:
            checks.append(AiderPreflightCheck(
                check_name="aider_importable",
                passed=False,
                detail="timeout checking aider import",
            ))
            unknown = True
        except (FileNotFoundError, OSError) as exc:
            checks.append(AiderPreflightCheck(
                check_name="aider_importable",
                passed=False,
                detail=str(exc),
            ))
            unknown = True

        # Check 2 (advisory): aider_version_detectable
        try:
            proc2 = subprocess.run(
                ["python3", "-c", "import aider; print(getattr(aider, '__version__', 'unknown'))"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            version_ok = proc2.returncode == 0 and bool(proc2.stdout.strip())
            checks.append(AiderPreflightCheck(
                check_name="aider_version_detectable",
                passed=version_ok,
                detail=proc2.stdout.strip() if version_ok else "version not detectable",
            ))
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            checks.append(AiderPreflightCheck(
                check_name="aider_version_detectable",
                passed=False,
                detail="could not detect version",
            ))

        # Check 3 (blocking): permission_gate_active
        gate_ok = self._gate is not None
        checks.append(AiderPreflightCheck(
            check_name="permission_gate_active",
            passed=gate_ok,
            detail="" if gate_ok else "no TypedPermissionGate provided",
        ))

        # Check 4 (blocking): config_keys_present
        required_keys = {"model", "edit_format"}
        config_ok = required_keys.issubset(set(self._config.keys()))
        checks.append(AiderPreflightCheck(
            check_name="config_keys_present",
            passed=config_ok,
            detail="" if config_ok else f"missing keys: {required_keys - set(self._config.keys())}",
        ))

        # Check 5 (advisory): working_tree_clean
        try:
            proc5 = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            clean = proc5.returncode == 0 and not proc5.stdout.strip()
            checks.append(AiderPreflightCheck(
                check_name="working_tree_clean",
                passed=clean,
                detail="" if clean else "working tree has changes",
            ))
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            checks.append(AiderPreflightCheck(
                check_name="working_tree_clean",
                passed=False,
                detail="could not check git status",
            ))

        blocking_names = {"aider_importable", "permission_gate_active", "config_keys_present"}
        blocking_checks = tuple(c for c in checks if c.check_name in blocking_names)
        blocking_passed = all(c.passed for c in blocking_checks)

        if unknown:
            verdict = "unknown"
        elif blocking_passed:
            verdict = "ready"
        else:
            verdict = "not_ready"

        return AiderPreflightResult(
            verdict=verdict,
            checks=tuple(checks),
            blocking_checks=blocking_checks,
            evaluated_at=_iso_now(),
        )


def emit_preflight_artifact(
    result: AiderPreflightResult,
    *,
    artifact_dir: Path = _DEFAULT_ARTIFACT_DIR,
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "aider_preflight_result.json"
    out_path.write_text(
        json.dumps(
            {
                "verdict": result.verdict,
                "evaluated_at": result.evaluated_at,
                "blocking_checks": [
                    {"check_name": c.check_name, "passed": c.passed, "detail": c.detail}
                    for c in result.blocking_checks
                ],
                "checks": [
                    {"check_name": c.check_name, "passed": c.passed, "detail": c.detail}
                    for c in result.checks
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = [
    "AiderPreflightCheck",
    "AiderPreflightResult",
    "AiderPreflightChecker",
    "emit_preflight_artifact",
]
