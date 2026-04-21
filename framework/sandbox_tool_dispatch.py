"""Typed dispatch bridge: RunCommandAction/RunTestsAction → LocalSandboxRunner.

Callers are responsible for permission checks before invoking dispatch functions.
The runner parameter is optional; when omitted, a LocalSandboxRunner is
created with the action's timeout_seconds.
"""
from __future__ import annotations

import re
from typing import Optional

from framework.sandbox import LocalSandboxRunner, SandboxResult
from framework.tool_schema import (
    RunCommandAction,
    RunCommandObservation,
    RunTestsAction,
    RunTestsObservation,
)
from framework.workspace_scope import ToolPathScope


def dispatch_run_command(
    action: RunCommandAction,
    scope: ToolPathScope,
    *,
    runner: Optional[LocalSandboxRunner] = None,
    extra_env: Optional[dict] = None,
) -> RunCommandObservation:
    if not isinstance(action, RunCommandAction):
        raise TypeError(f"Expected RunCommandAction; got {type(action)!r}")
    if not action.command.strip():
        return RunCommandObservation(
            stdout="",
            stderr="error: empty command",
            exit_code=1,
            error="empty command",
        )
    effective_runner = runner or LocalSandboxRunner(timeout_seconds=action.timeout_seconds)
    cwd_str = action.cwd if action.cwd and action.cwd != "." else str(scope.source_root)
    cwd = scope.resolve_path(cwd_str)
    env = dict(action.env)
    if extra_env:
        env.update(extra_env)
    result: SandboxResult = effective_runner.run_command(
        command=action.command,
        cwd=cwd,
        env=env if env else None,
    )
    return RunCommandObservation(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.return_code,
    )


def dispatch_run_tests(
    action: RunTestsAction,
    scope: ToolPathScope,
    *,
    runner: Optional[LocalSandboxRunner] = None,
    extra_env: Optional[dict] = None,
) -> RunTestsObservation:
    if not isinstance(action, RunTestsAction):
        raise TypeError(f"Expected RunTestsAction; got {type(action)!r}")
    effective_runner = runner or LocalSandboxRunner(timeout_seconds=action.timeout_seconds)
    test_targets = list(action.test_paths) if action.test_paths else ["tests"]
    parts = ["python3", "-m", "pytest"] + test_targets + ["--tb=short", "-q"]
    parts += list(action.extra_args)
    command = " ".join(parts)
    cwd = scope.source_root
    env = dict(extra_env) if extra_env else None
    result: SandboxResult = effective_runner.run_command(
        command=command,
        cwd=cwd,
        env=env,
    )
    passed, failed, skipped = _parse_pytest_summary(result.stdout)
    return RunTestsObservation(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.return_code,
        passed=passed,
        failed=failed,
        skipped=skipped,
    )


def _parse_pytest_summary(output: str) -> tuple:
    passed = failed = skipped = 0
    for line in output.splitlines():
        m = re.search(r"(\d+) passed", line)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+) failed", line)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+) skipped", line)
        if m:
            skipped = int(m.group(1))
    return passed, failed, skipped


__all__ = ["dispatch_run_command", "dispatch_run_tests"]
