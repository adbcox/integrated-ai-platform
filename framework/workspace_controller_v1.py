"""Workspace descriptor and controller skeleton for the minimum substrate (Phase 2, P2-01)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkspaceDescriptorV1:
    source_root: str
    scratch_root: str
    artifact_root: str
    source_read_only: bool = True


class WorkspaceControllerV1:
    def __init__(self, descriptor: WorkspaceDescriptorV1) -> None:
        self.descriptor = descriptor

    def validate_layout(self) -> bool:
        """Structural validation only — no filesystem I/O at this layer."""
        d = self.descriptor
        if not d.source_root:
            return False
        if not d.scratch_root:
            return False
        if not d.artifact_root:
            return False
        # scratch and source must be distinct
        if d.scratch_root == d.source_root:
            return False
        # artifact_root must not be a /tmp path (workspace contract rule)
        if d.artifact_root.startswith("/tmp"):
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "source_root": self.descriptor.source_root,
            "scratch_root": self.descriptor.scratch_root,
            "artifact_root": self.descriptor.artifact_root,
            "source_read_only": self.descriptor.source_read_only,
            "layout_valid": self.validate_layout(),
        }
