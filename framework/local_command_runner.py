"""Normalized local execution wrapper for framework make targets.

Routes check, quick, and test_offline through a typed subprocess interface,
captures structured output, and emits CommandTelemetry.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from .runtime_telemetry_schema import CommandTelemetry

REPO_ROOT = Path(__file__).resolve().parents[1]

KNOWN_FRAMEWORK_COMMANDS: dict[str, str] = {
    "check": "make check",
    "quick": "make quick",
    "test_offline": "make test-offline",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class LocalCommandResult:
    command_name: str
    argv: str
    cwd: str
    return_code: int
    stdout: str
    stderr: str
    started_at: str
    completed_at: str
    duration_ms: int
    success: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_name": self.command_name,
            "argv": self.argv,
            "cwd": self.cwd,
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "success": self.success,
        }

    def to_telemetry(self) -> CommandTelemetry:
        return CommandTelemetry(
            command=self.argv,
            cwd=self.cwd,
            return_code=self.return_code,
            stdout=self.stdout,
            stderr=self.stderr,
            started_at=self.started_at,
            completed_at=self.completed_at,
            duration_ms=self.duration_ms,
            success=self.success,
        )


class LocalCommandRunner:
    """Run framework make targets through a normalized typed interface."""

    def __init__(self, *, cwd: Path | None = None, timeout_seconds: int = 300) -> None:
        self._cwd = (cwd or REPO_ROOT).resolve()
        self._timeout_seconds = timeout_seconds

    def run(self, command_name: str) -> LocalCommandResult:
        if command_name not in KNOWN_FRAMEWORK_COMMANDS:
            raise ValueError(
                f"unknown command {command_name!r}; "
                f"known commands: {sorted(KNOWN_FRAMEWORK_COMMANDS)}"
            )
        argv = KNOWN_FRAMEWORK_COMMANDS[command_name]
        started_at = _iso_now()
        t0 = perf_counter()
        try:
            proc = subprocess.run(
                ["bash", "-lc", argv],
                capture_output=True,
                text=True,
                cwd=str(self._cwd),
                timeout=self._timeout_seconds,
            )
            return_code = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            return_code = -1
            stdout = ""
            stderr = f"TimeoutExpired after {self._timeout_seconds}s: {exc}"
        except Exception as exc:  # noqa: BLE001
            return_code = -1
            stdout = ""
            stderr = f"{type(exc).__name__}: {exc}"
        completed_at = _iso_now()
        duration_ms = int((perf_counter() - t0) * 1000)
        return LocalCommandResult(
            command_name=command_name,
            argv=argv,
            cwd=str(self._cwd),
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            success=(return_code == 0),
        )


__all__ = ["KNOWN_FRAMEWORK_COMMANDS", "LocalCommandResult", "LocalCommandRunner"]
