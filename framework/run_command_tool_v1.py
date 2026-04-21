"""Minimal run_command tool skeleton for the Phase 2 substrate (P2-02)."""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class RunCommandResultV1:
    status: str          # success | failure | timeout | error
    command: Union[str, List[str]]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    side_effecting: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "side_effecting": self.side_effecting,
            "error": self.error,
        }


class RunCommandToolV1:
    TOOL_NAME = "run_command"
    SIDE_EFFECTING = True
    DEFAULT_TIMEOUT = 120

    def run(
        self,
        command: Union[str, List[str]],
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        success_exit_codes: Optional[List[int]] = None,
    ) -> RunCommandResultV1:
        timeout = timeout or self.DEFAULT_TIMEOUT
        success_exit_codes = success_exit_codes or [0]
        shell = isinstance(command, str)
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            duration_ms = int((time.monotonic() - t0) * 1000)
            status = "success" if proc.returncode in success_exit_codes else "failure"
            return RunCommandResultV1(
                status=status,
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return RunCommandResultV1(
                status="timeout", command=command, exit_code=-1,
                stdout="", stderr="Command terminated by timeout",
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return RunCommandResultV1(
                status="error", command=command, exit_code=-1,
                stdout="", stderr="", duration_ms=duration_ms, error=str(exc),
            )
