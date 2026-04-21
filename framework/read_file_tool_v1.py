"""Minimal read_file tool implementation for the Phase 2 substrate (P2-02)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ReadFileResultV1:
    status: str          # success | not_found | error
    content: Optional[str]
    path: str
    line_count: int
    truncated: bool
    side_effecting: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "content": self.content,
            "path": self.path,
            "line_count": self.line_count,
            "truncated": self.truncated,
            "side_effecting": self.side_effecting,
            "error": self.error,
        }


class ReadFileToolV1:
    TOOL_NAME = "read_file"
    SIDE_EFFECTING = False
    MAX_BYTES = 65536  # 64 KB truncation limit

    def run(self, path: str, offset: int = 0, limit: Optional[int] = None) -> ReadFileResultV1:
        p = Path(path)
        if not p.exists():
            return ReadFileResultV1(
                status="not_found", content=None, path=path,
                line_count=0, truncated=False, error=f"path not found: {path}",
            )
        try:
            raw = p.read_bytes()
            truncated = len(raw) > self.MAX_BYTES
            if truncated:
                raw = raw[: self.MAX_BYTES]
            text = raw.decode("utf-8", errors="replace")
            lines = text.splitlines()
            if offset:
                lines = lines[offset:]
            if limit is not None:
                lines = lines[:limit]
            content = "\n".join(lines)
            return ReadFileResultV1(
                status="success", content=content, path=path,
                line_count=len(lines), truncated=truncated,
            )
        except Exception as exc:
            return ReadFileResultV1(
                status="error", content=None, path=path,
                line_count=0, truncated=False, error=str(exc),
            )
