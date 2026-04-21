"""DiffResultPackager: packages post-patch git diff into a DiffResultPackage."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from framework.git_diff_dispatch import dispatch_git_diff
from framework.tool_schema import GitDiffAction, GitDiffObservation
from framework.workspace_scope import ToolPathScope

# -- import-time assertions --
assert "diff" in GitDiffObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: GitDiffObservation.diff"
assert "error" in GitDiffObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: GitDiffObservation.error"
assert callable(dispatch_git_diff), \
    "INTERFACE MISMATCH: dispatch_git_diff"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class DiffResultPackage:
    session_id: str
    diff: str
    diff_error: Optional[str]
    ref: Optional[str]
    packaged_at: str


class DiffResultPackager:
    """Calls dispatch_git_diff and packages the result; runner-injectable; error non-raising."""

    def __init__(self, *, runner=None, source_root=None):
        self._runner = runner
        from pathlib import Path
        self._source_root = Path(source_root) if source_root is not None else Path(".")

    def package(
        self,
        session_id: str,
        *,
        ref: Optional[str] = None,
        path: str = ".",
        scope: Optional[ToolPathScope] = None,
    ) -> DiffResultPackage:
        diff_text = ""
        diff_error: Optional[str] = None
        try:
            action = GitDiffAction(path=path, ref=ref)
            eff_scope = scope if scope is not None else ToolPathScope(source_root=self._source_root)
            kwargs = {}
            if self._runner is not None:
                kwargs["runner"] = self._runner
            obs: GitDiffObservation = dispatch_git_diff(action, eff_scope, **kwargs)
            diff_text = obs.diff or ""
            diff_error = obs.error
        except Exception as exc:
            diff_error = str(exc)

        return DiffResultPackage(
            session_id=session_id,
            diff=diff_text,
            diff_error=diff_error,
            ref=ref,
            packaged_at=_iso_now(),
        )


__all__ = ["DiffResultPackage", "DiffResultPackager"]
