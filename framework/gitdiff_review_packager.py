"""GitDiffReviewPackager — adopts dispatch_git_diff for post-task diff evidence.

Inspection gate output:
  dispatch_git_diff sig: (action: GitDiffAction, scope: ToolPathScope, *, runner: Optional[Any] = None) -> GitDiffObservation
  GitDiffAction fields: ['path', 'ref']
  GitDiffObservation fields: ['diff', 'error']
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.git_diff_dispatch import dispatch_git_diff
from framework.tool_schema import GitDiffAction, GitDiffObservation
from framework.workspace_scope import ToolPathScope

assert callable(dispatch_git_diff), "INTERFACE MISMATCH: dispatch_git_diff not callable"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class DiffReviewRecord:
    target_path: str
    diff_text: str
    line_count: int
    has_changes: bool
    packaged_at: str

    def is_empty(self) -> bool:
        return not self.has_changes

    def to_dict(self) -> dict:
        return {
            "target_path": self.target_path,
            "diff_text": self.diff_text,
            "line_count": self.line_count,
            "has_changes": self.has_changes,
            "packaged_at": self.packaged_at,
        }


class GitDiffReviewPackager:
    """Adopts dispatch_git_diff for loop post-task diff packaging."""

    def __init__(self, source_root: Optional[Path] = None) -> None:
        self._source_root = Path(source_root) if source_root is not None else Path(".")

    def package_diff(self, target_path: str, *, ref: str = "HEAD") -> DiffReviewRecord:
        try:
            action = GitDiffAction(path=target_path, ref=ref)
            scope = ToolPathScope(source_root=self._source_root)
            obs = dispatch_git_diff(action, scope)
            if obs.error or not obs.diff:
                return DiffReviewRecord(
                    target_path=target_path,
                    diff_text="",
                    line_count=0,
                    has_changes=False,
                    packaged_at=_iso_now(),
                )
            diff_text = obs.diff
            line_count = len(diff_text.splitlines())
            has_changes = bool(diff_text.strip())
            return DiffReviewRecord(
                target_path=target_path,
                diff_text=diff_text,
                line_count=line_count,
                has_changes=has_changes,
                packaged_at=_iso_now(),
            )
        except Exception as exc:  # noqa: BLE001
            return DiffReviewRecord(
                target_path=target_path,
                diff_text="",
                line_count=0,
                has_changes=False,
                packaged_at=_iso_now(),
            )


__all__ = ["DiffReviewRecord", "GitDiffReviewPackager"]
