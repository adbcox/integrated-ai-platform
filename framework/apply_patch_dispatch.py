"""Pure-Python scope-gated patch dispatch for ApplyPatchAction."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from framework.tool_schema import ApplyPatchAction, ApplyPatchObservation
from framework.workspace_scope import ToolPathScope


def dispatch_apply_patch(
    action: ApplyPatchAction,
    scope: ToolPathScope,
) -> ApplyPatchObservation:
    if not isinstance(action, ApplyPatchAction):
        raise TypeError(f"Expected ApplyPatchAction; got {type(action)!r}")
    if not action.old_string:
        return ApplyPatchObservation(path=action.path, applied=False, error="empty old_string rejected")

    try:
        target = scope.resolve_path(action.path, writable=True)
    except PermissionError as exc:
        return ApplyPatchObservation(path=action.path, applied=False, error=str(exc))

    try:
        original = target.read_text(encoding="utf-8")
    except OSError as exc:
        return ApplyPatchObservation(path=action.path, applied=False, error=str(exc))

    if action.old_string not in original:
        return ApplyPatchObservation(
            path=action.path, applied=False, error=f"old_string not found in {target}"
        )

    if action.replace_all:
        updated = original.replace(action.old_string, action.new_string)
    else:
        updated = original.replace(action.old_string, action.new_string, 1)

    try:
        target.write_text(updated, encoding="utf-8")
    except OSError as exc:
        return ApplyPatchObservation(path=action.path, applied=False, error=str(exc))

    return ApplyPatchObservation(path=action.path, applied=True)


__all__ = ["dispatch_apply_patch"]
