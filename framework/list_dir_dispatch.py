"""Bounded dispatch for ListDirAction -> ListDirObservation via local filesystem."""
from __future__ import annotations

from framework.tool_schema import ListDirAction, ListDirObservation
from framework.workspace_scope import ToolPathScope


def dispatch_list_dir(action: ListDirAction, scope: ToolPathScope) -> ListDirObservation:
    if not isinstance(action, ListDirAction):
        raise TypeError(f"Expected ListDirAction; got {type(action)!r}")
    try:
        target = scope.resolve_path(action.path, writable=False)
    except PermissionError as exc:
        return ListDirObservation(path=action.path, entries=(), error=str(exc))
    try:
        raw = list(target.iterdir())
    except FileNotFoundError:
        return ListDirObservation(path=action.path, entries=(), error=f"not found: {target}")
    except NotADirectoryError:
        return ListDirObservation(path=action.path, entries=(), error=f"not a directory: {target}")
    except PermissionError as exc:
        return ListDirObservation(path=action.path, entries=(), error=str(exc))
    entries = tuple(
        sorted(f"{e.name} [{'dir' if e.is_dir() else 'file'}]" for e in raw)
    )
    return ListDirObservation(path=action.path, entries=entries, error=None)


__all__ = ["dispatch_list_dir"]
