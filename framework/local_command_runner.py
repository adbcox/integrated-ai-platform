"""Phase 1 wrapped local command runner.

Thin, testable wrapper for build/test/lint/general command execution.
Validation pack code must not shell out directly; all local command
execution in Phase 1 flows through this runner so telemetry is
normalized and the workspace contract stays intact.
"""

from __future__ import annotations

import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Mapping

from .runtime_telemetry_schema import CommandTelemetry


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "...<truncated>"


class LocalCommandRunner:
    """Bounded local command runner that produces normalized telemetry."""

    def __init__(
        self,
        *,
        default_timeout_seconds: int = 120,
        stdout_byte_limit: int = 8192,
        stderr_byte_limit: int = 8192,
    ) -> None:
        self._default_timeout = max(1, int(default_timeout_seconds))
        self._stdout_limit = max(0, int(stdout_byte_limit))
        self._stderr_limit = max(0, int(stderr_byte_limit))

    def run(
        self,
        command: str | list[str],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> CommandTelemetry:
        if isinstance(command, list):
            argv = list(command)
            command_str = " ".join(shlex.quote(a) for a in argv)
            shell = False
        else:
            argv = command
            command_str = command
            shell = True

        started_at = _iso_now()
        t0 = perf_counter()
        timeout = int(timeout_seconds) if timeout_seconds else self._default_timeout
        run_env = dict(env) if env else None
        try:
            proc = subprocess.run(
                argv,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                shell=shell,
                timeout=timeout,
                env=run_env,
                check=False,
            )
            return_code = int(proc.returncode)
            stdout = _truncate(proc.stdout or "", self._stdout_limit)
            stderr = _truncate(proc.stderr or "", self._stderr_limit)
        except subprocess.TimeoutExpired as exc:
            return_code = 124
            stdout = _truncate(exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""), self._stdout_limit)
            stderr = _truncate(
                (exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or ""))
                + f"\n[timeout after {timeout}s]",
                self._stderr_limit,
            )
        except FileNotFoundError as exc:
            return_code = 127
            stdout = ""
            stderr = f"command not found: {exc}"
        completed_at = _iso_now()
        duration_ms = int((perf_counter() - t0) * 1000)
        return CommandTelemetry(
            command=command_str,
            cwd=str(cwd),
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            success=(return_code == 0),
        )


__all__ = ["LocalCommandRunner"]
