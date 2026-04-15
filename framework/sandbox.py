"""Sandbox execution adapter for bounded local command execution."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class SandboxResult:
    return_code: int
    stdout: str
    stderr: str


class LocalSandboxRunner:
    """Local bounded sandbox runner.

    This adapter intentionally keeps worker logic backend-agnostic so we can later
    swap to gVisor/firecracker without touching worker orchestration.
    """

    def __init__(self, *, mode: str = "local_bounded", timeout_seconds: int = 1200) -> None:
        self.mode = mode
        self.timeout_seconds = max(1, int(timeout_seconds))

    def run_command(
        self,
        *,
        command: str,
        cwd: Path,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult:
        run_env = os.environ.copy()
        if env:
            run_env.update({str(k): str(v) for k, v in env.items()})
        run_env["FRAMEWORK_SANDBOX_MODE"] = self.mode
        proc = subprocess.run(
            ["bash", "-lc", command],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            env=run_env,
            timeout=self.timeout_seconds,
        )
        return SandboxResult(
            return_code=int(proc.returncode),
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
