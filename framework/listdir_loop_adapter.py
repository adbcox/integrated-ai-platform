"""ListDirLoopAdapter — adopts dispatch_list_dir for loop pre-task path discovery.

Inspection gate output:
  dispatch_list_dir sig: (action: ListDirAction, scope: ToolPathScope) -> ListDirObservation
  ListDirAction fields: ['path']
  ListDirObservation fields: ['path', 'entries', 'error']
  entries format: tuple of "<name> [file]" or "<name> [dir]" strings
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.list_dir_dispatch import dispatch_list_dir
from framework.tool_schema import ListDirAction, ListDirObservation
from framework.workspace_scope import ToolPathScope

assert callable(dispatch_list_dir), "INTERFACE MISMATCH: dispatch_list_dir not callable"
assert "path" in ListDirAction.__dataclass_fields__, "INTERFACE MISMATCH: ListDirAction.path missing"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class DirEntry:
    path: str
    is_file: bool
    is_dir: bool


@dataclass
class DirListing:
    root_path: str
    entries: list
    listed_at: str
    entry_count: int

    def file_paths(self) -> list:
        return [e.path for e in self.entries if e.is_file]

    def to_snippet(self) -> str:
        if not self.entries:
            return f"[empty directory: {self.root_path}]"
        lines = [f"Directory: {self.root_path}"]
        for e in self.entries:
            kind = "file" if e.is_file else "dir"
            lines.append(f"  {e.path} [{kind}]")
        return "\n".join(lines)


def _parse_entry(root_path: str, raw: str) -> DirEntry:
    if raw.endswith(" [file]"):
        name = raw[: -len(" [file]")]
        return DirEntry(path=f"{root_path}/{name}".lstrip("/"), is_file=True, is_dir=False)
    elif raw.endswith(" [dir]"):
        name = raw[: -len(" [dir]")]
        return DirEntry(path=f"{root_path}/{name}".lstrip("/"), is_file=False, is_dir=True)
    else:
        return DirEntry(path=f"{root_path}/{raw}".lstrip("/"), is_file=True, is_dir=False)


class ListDirLoopAdapter:
    """Adopts dispatch_list_dir for loop pre-task directory inspection."""

    def __init__(self, source_root: Optional[Path] = None) -> None:
        self._source_root = Path(source_root) if source_root is not None else Path(".")

    def list_dir(self, path: str) -> DirListing:
        try:
            resolved = (self._source_root / path).resolve()
            action = ListDirAction(path=str(resolved))
            scope = ToolPathScope(source_root=self._source_root)
            obs = dispatch_list_dir(action, scope)
            if obs.error or not obs.entries:
                return DirListing(
                    root_path=path,
                    entries=[],
                    listed_at=_iso_now(),
                    entry_count=0,
                )
            entries = [_parse_entry(path, raw) for raw in obs.entries]
            return DirListing(
                root_path=path,
                entries=entries,
                listed_at=_iso_now(),
                entry_count=len(entries),
            )
        except Exception as exc:  # noqa: BLE001
            return DirListing(
                root_path=path,
                entries=[],
                listed_at=_iso_now(),
                entry_count=0,
            )


__all__ = ["DirEntry", "DirListing", "ListDirLoopAdapter"]
