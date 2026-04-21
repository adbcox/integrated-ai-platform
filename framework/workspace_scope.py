"""Typed path-scope contract for tool dispatch.

ToolPathScope declares which paths are read-only vs writable for a given
tool call. Does not implement sandboxing or permission policy.

Factory helpers bridge from existing workspace abstractions without modifying them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.runtime_workspace_contract import RuntimeWorkspace
    from framework.workspace import WorkspaceContext


@dataclass(frozen=True)
class ToolPathScope:
    source_root: Path
    writable_roots: tuple = ()

    def resolve_path(self, candidate: "str | Path", *, writable: bool = False) -> Path:
        resolved = Path(candidate).resolve()
        if writable:
            try:
                resolved.relative_to(self.source_root.resolve())
                raise PermissionError(
                    f"Write blocked: {resolved} is inside source_root {self.source_root}"
                )
            except ValueError:
                pass
            for wr in self.writable_roots:
                try:
                    resolved.relative_to(Path(wr).resolve())
                    return resolved
                except ValueError:
                    continue
            raise PermissionError(
                f"Write blocked: {resolved} is not under any writable root"
            )
        return resolved

    def is_writable(self, candidate: "str | Path") -> bool:
        try:
            self.resolve_path(candidate, writable=True)
            return True
        except PermissionError:
            return False


def scope_from_runtime_workspace(ws: "RuntimeWorkspace") -> ToolPathScope:
    return ToolPathScope(
        source_root=ws.source_root.resolve(),
        writable_roots=(ws.scratch_root.resolve(), ws.artifact_root.resolve()),
    )


def scope_from_workspace_context(ctx: "WorkspaceContext") -> ToolPathScope:
    return ToolPathScope(
        source_root=ctx.repo_root.resolve(),
        writable_roots=(ctx.worktree_target.resolve(), ctx.artifact_root.resolve()),
    )


__all__ = ["ToolPathScope", "scope_from_runtime_workspace", "scope_from_workspace_context"]
