"""Bounded dispatch for GitDiffAction -> GitDiffObservation via scoped git subprocess."""
from __future__ import annotations

import subprocess
from typing import Any, Optional

from framework.tool_schema import GitDiffAction, GitDiffObservation
from framework.workspace_scope import ToolPathScope


def dispatch_git_diff(
    action: GitDiffAction,
    scope: ToolPathScope,
    *,
    runner: Optional[Any] = None,
) -> GitDiffObservation:
    if not isinstance(action, GitDiffAction):
        raise TypeError(f"Expected GitDiffAction; got {type(action)!r}")
    try:
        cwd = scope.resolve_path(action.path, writable=False)
    except PermissionError as exc:
        return GitDiffObservation(diff="", error=str(exc))

    cmd = ["git", "diff"]
    if action.ref:
        cmd.append(action.ref)

    try:
        if runner is not None:
            result = runner.run_command(command=" ".join(cmd), cwd=str(cwd))
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            rc = result.return_code
        else:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=30,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            rc = proc.returncode
    except subprocess.TimeoutExpired:
        return GitDiffObservation(diff="", error="git diff timed out")
    except FileNotFoundError:
        return GitDiffObservation(diff="", error="git not found in PATH")
    except OSError as exc:
        return GitDiffObservation(diff="", error=str(exc))

    if rc != 0 and not stdout:
        return GitDiffObservation(diff="", error=stderr.strip() or f"git diff exited {rc}")
    return GitDiffObservation(diff=stdout, error=None)


__all__ = ["dispatch_git_diff"]
