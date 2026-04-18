"""Phase 1 deterministic workspace/artifact contract.

Explicit, repeatable local-run layout. Any Phase 1 local route resolves
three roots from a single call:

- source_root:   read-only by contract (the repo tree itself)
- scratch_root:  writable scratch workspace, deterministic per run
- artifact_root: writable artifact destination, deterministic per run

Callers must never write directly into source_root. The validation
pack and artifact service enforce the contract by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeWorkspace:
    run_id: str
    session_id: str
    source_root: Path
    scratch_root: Path
    artifact_root: Path

    def ensure_materialized(self) -> "RuntimeWorkspace":
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        return self

    def to_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "source_root": str(self.source_root),
            "scratch_root": str(self.scratch_root),
            "artifact_root": str(self.artifact_root),
        }


def build_workspace(
    *,
    source_root: Path,
    base_root: Path,
    run_id: str,
    session_id: str,
) -> RuntimeWorkspace:
    """Return a deterministic ``RuntimeWorkspace`` for a run_id/session_id pair.

    ``base_root`` is the directory under which per-run scratch and
    artifact trees are created. The function does not touch disk unless
    ``ensure_materialized`` is called.
    """
    if not run_id:
        raise ValueError("run_id must be non-empty")
    if not session_id:
        raise ValueError("session_id must be non-empty")
    source_root = source_root.resolve()
    base_root = base_root.resolve()
    scratch_root = base_root / "scratch" / session_id / run_id
    artifact_root = base_root / "artifacts" / session_id / run_id
    return RuntimeWorkspace(
        run_id=run_id,
        session_id=session_id,
        source_root=source_root,
        scratch_root=scratch_root,
        artifact_root=artifact_root,
    )


def assert_read_only_source(workspace: RuntimeWorkspace, candidate: Path) -> None:
    """Raise if ``candidate`` is inside ``source_root``.

    Phase 1 enforces the contract that writes must go to scratch_root or
    artifact_root, not back into source_root.
    """
    try:
        candidate.resolve().relative_to(workspace.source_root)
    except ValueError:
        return
    raise PermissionError(
        f"write target {candidate} is inside source_root {workspace.source_root}; "
        "Phase 1 workspace contract forbids writes to source_root"
    )


__all__ = [
    "RuntimeWorkspace",
    "assert_read_only_source",
    "build_workspace",
]
