"""Aider-under-runtime adapter implementation for LAEC1.

Routes Aider via LocalCommandRunner behind AiderAdapterPolicy.
Dry-run path does not spawn subprocesses.

Inspection gate output:
  LocalCommandRunner.run signature: (self, command_name: str) -> LocalCommandResult
  AiderPreflightChecker.run_preflight signature: (self) -> AiderPreflightResult
  LocalCommandResult fields: command_name, argv, cwd, return_code, stdout, stderr,
    started_at, completed_at, duration_ms, success
  AiderPreflightResult fields: verdict, checks, blocking_checks, evaluated_at, artifact_path
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.aider_adapter_contract import (
    AiderAdapterArtifact,
    AiderAdapterConfig,
    AiderAdapterPolicy,
    AiderAdapterRequest,
    DEFAULT_AIDER_POLICY,
)
from framework.local_command_runner import LocalCommandRunner
from framework.aider_preflight import AiderPreflightChecker

_EXPERIMENTAL_FLAG = True


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AiderRuntimeAdapter:
    """Controlled Aider adapter routing through LocalCommandRunner."""

    def __init__(
        self,
        command_runner: Optional[LocalCommandRunner] = None,
        policy: Optional[AiderAdapterPolicy] = None,
        preflight_checker: Optional[AiderPreflightChecker] = None,
    ) -> None:
        self._runner = command_runner or LocalCommandRunner()
        self._policy = policy or DEFAULT_AIDER_POLICY
        self._preflight_checker = preflight_checker

    def preflight(self) -> dict:
        checker = self._preflight_checker if self._preflight_checker is not None else AiderPreflightChecker()
        result = checker.run_preflight()
        return {
            "verdict": result.verdict,
            "blocking_checks": len(result.blocking_checks),
            "evaluated_at": result.evaluated_at,
        }

    def run(
        self,
        request: AiderAdapterRequest,
        *,
        dry_run: Optional[bool] = None,
    ) -> AiderAdapterArtifact:
        effective_dry_run = dry_run if dry_run is not None else self._policy.dry_run_default

        # Validate config
        config = request.config
        errors = config.validate()
        if errors:
            return AiderAdapterArtifact(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="; ".join(errors),
                dry_run=effective_dry_run,
                model=config.model,
                target_files=list(config.target_files),
                session_id=request.session_id,
            )

        if effective_dry_run:
            return AiderAdapterArtifact(
                success=True,
                exit_code=0,
                stdout=f"[dry-run] would run aider model={config.model} files={config.target_files}",
                stderr="",
                dry_run=True,
                model=config.model,
                target_files=list(config.target_files),
                session_id=request.session_id,
            )

        # Live path: run via LocalCommandRunner with known command name
        # "aider" must be in KNOWN_FRAMEWORK_COMMANDS for this to succeed;
        # if not present, LocalCommandRunner.run will raise/return failure gracefully
        try:
            cmd_result = self._runner.run("aider")
            return AiderAdapterArtifact(
                success=cmd_result.success,
                exit_code=cmd_result.return_code,
                stdout=cmd_result.stdout,
                stderr=cmd_result.stderr,
                dry_run=False,
                model=config.model,
                target_files=list(config.target_files),
                session_id=request.session_id,
            )
        except Exception as exc:
            return AiderAdapterArtifact(
                success=False,
                exit_code=-2,
                stdout="",
                stderr=str(exc),
                dry_run=False,
                model=config.model,
                target_files=list(config.target_files),
                session_id=request.session_id,
            )


__all__ = [
    "_EXPERIMENTAL_FLAG",
    "AiderRuntimeAdapter",
]
