"""Pure-Python ReadFileAction dispatch over ToolPathScope."""
from __future__ import annotations

from framework.tool_schema import ReadFileAction, ReadFileObservation
from framework.workspace_scope import ToolPathScope


def dispatch_read_file(
    action: ReadFileAction,
    scope: ToolPathScope,
) -> ReadFileObservation:
    if not isinstance(action, ReadFileAction):
        raise TypeError(f"Expected ReadFileAction; got {type(action)!r}")

    target = scope.resolve_path(action.path)

    try:
        content = target.read_text(encoding="utf-8")
        return ReadFileObservation(path=action.path, content=content)
    except FileNotFoundError:
        return ReadFileObservation(path=action.path, content="", error=f"file not found: {target}")
    except OSError as exc:
        return ReadFileObservation(path=action.path, content="", error=str(exc))


__all__ = ["dispatch_read_file"]
