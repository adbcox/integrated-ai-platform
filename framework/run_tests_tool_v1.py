"""Minimal run_tests tool skeleton for the Phase 2 substrate (P2-02)."""
from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RunTestsResultV1:
    status: str          # success | failure | timeout | error
    test_target: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    passed: int = 0
    failed: int = 0
    errors: int = 0
    side_effecting: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "test_target": self.test_target,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "side_effecting": self.side_effecting,
            "error": self.error,
        }


def _parse_pytest_summary(stdout: str) -> dict:
    """Extract passed/failed/error counts from pytest output."""
    m = re.search(r"(\d+) passed", stdout)
    passed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) failed", stdout)
    failed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) error", stdout)
    errors = int(m.group(1)) if m else 0
    return {"passed": passed, "failed": failed, "errors": errors}


class RunTestsToolV1:
    TOOL_NAME = "run_tests"
    SIDE_EFFECTING = False
    DEFAULT_TIMEOUT = 180

    def run(
        self,
        test_target: str,
        timeout: Optional[int] = None,
        extra_args: Optional[list] = None,
        cwd: Optional[str] = None,
    ) -> RunTestsResultV1:
        import sys
        timeout = timeout or self.DEFAULT_TIMEOUT
        cmd = [sys.executable, "-m", "pytest", test_target, "-v"]
        if extra_args:
            cmd.extend(extra_args)
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd,
            )
            duration_ms = int((time.monotonic() - t0) * 1000)
            counts = _parse_pytest_summary(proc.stdout)
            status = "success" if proc.returncode == 0 else "failure"
            return RunTestsResultV1(
                status=status,
                test_target=test_target,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
                **counts,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return RunTestsResultV1(
                status="timeout", test_target=test_target, exit_code=-1,
                stdout="", stderr="Test run terminated by timeout", duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return RunTestsResultV1(
                status="error", test_target=test_target, exit_code=-1,
                stdout="", stderr="", duration_ms=duration_ms, error=str(exc),
            )
