"""Workspace controller abstraction for framework jobs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .job_schema import Job


@dataclass(frozen=True)
class WorkspaceContext:
    repo_root: Path
    worktree_target: Path
    artifact_root: Path


class WorkspaceController:
    """Creates deterministic workspace context for tool execution."""

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root.resolve()

    def for_job(self, job: Job) -> WorkspaceContext:
        repo_root = job.repo_root_path
        worktree_target = Path(job.target.worktree_target).resolve()
        workspace_artifacts = self.artifact_root / "workspace" / job.job_id
        workspace_artifacts.mkdir(parents=True, exist_ok=True)
        return WorkspaceContext(
            repo_root=repo_root,
            worktree_target=worktree_target,
            artifact_root=workspace_artifacts,
        )

    @staticmethod
    def resolve_in_repo(workspace: WorkspaceContext, candidate: str) -> Path:
        path = Path(candidate)
        if path.is_absolute():
            return path
        return (workspace.repo_root / path).resolve()
