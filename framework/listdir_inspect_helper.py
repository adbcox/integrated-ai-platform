"""ListDirInspectHelper: discovers sibling files of a target path via ListDirLoopAdapter."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from framework.listdir_loop_adapter import ListDirLoopAdapter, DirListing, DirEntry

# -- import-time assertions --
assert "entries" in DirListing.__dataclass_fields__, \
    "INTERFACE MISMATCH: DirListing.entries"
assert "entry_count" in DirListing.__dataclass_fields__, \
    "INTERFACE MISMATCH: DirListing.entry_count"
assert callable(getattr(ListDirLoopAdapter, "list_dir", None)), \
    "INTERFACE MISMATCH: ListDirLoopAdapter.list_dir"


@dataclass(frozen=True)
class TargetDiscoveryResult:
    target_path: str
    target_dir: str
    sibling_names: Tuple[str, ...]
    sibling_count: int
    discovery_error: Optional[str]


class ListDirInspectHelper:
    """Discovers sibling files of a target path; failure is non-blocking."""

    def __init__(self, *, adapter: Optional[ListDirLoopAdapter] = None):
        self._adapter = adapter or ListDirLoopAdapter()

    def discover(self, target_path: str) -> TargetDiscoveryResult:
        target_dir = str(Path(target_path).parent)
        siblings: Tuple[str, ...] = ()
        discovery_error: Optional[str] = None
        try:
            listing: DirListing = self._adapter.list_dir(target_dir)
            siblings = tuple(
            getattr(e, "name", None) or str(getattr(e, "path", ""))
            for e in listing.entries
        )
        except Exception as exc:
            discovery_error = str(exc)
        return TargetDiscoveryResult(
            target_path=target_path,
            target_dir=target_dir,
            sibling_names=siblings,
            sibling_count=len(siblings),
            discovery_error=discovery_error,
        )


__all__ = ["TargetDiscoveryResult", "ListDirInspectHelper"]
