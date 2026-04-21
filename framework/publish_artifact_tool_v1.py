"""Minimal publish_artifact tool implementation for the Phase 2 substrate (P2-02)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


@dataclass
class PublishArtifactResultV1:
    status: str          # success | error
    written_path: Optional[str]
    bytes_written: int
    side_effecting: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "written_path": self.written_path,
            "bytes_written": self.bytes_written,
            "side_effecting": self.side_effecting,
            "error": self.error,
        }


class PublishArtifactToolV1:
    TOOL_NAME = "publish_artifact"
    SIDE_EFFECTING = True

    def run(
        self,
        destination_path: str,
        payload: Union[dict, str, bytes],
    ) -> PublishArtifactResultV1:
        dest = Path(destination_path)
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(payload, dict):
                data = json.dumps(payload, indent=2).encode("utf-8")
            elif isinstance(payload, str):
                data = payload.encode("utf-8")
            else:
                data = payload
            dest.write_bytes(data)
            return PublishArtifactResultV1(
                status="success",
                written_path=str(dest),
                bytes_written=len(data),
            )
        except Exception as exc:
            return PublishArtifactResultV1(
                status="error",
                written_path=None,
                bytes_written=0,
                error=str(exc),
            )
