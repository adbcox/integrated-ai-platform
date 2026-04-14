"""Versioned trace schema for Manager-4 lane routing."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = REPO_ROOT / "artifacts" / "manager4"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
SCHEMA_VERSION = "trace-v1"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_commit_hash() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except subprocess.CalledProcessError:
        return None


@dataclass
class PromotionTraceEntry:
    schema_version: str = SCHEMA_VERSION
    timestamp: str = field(default_factory=_utc_timestamp)
    lane: str
    lane_label: str
    lane_status: str
    lane_reason: str
    stage: str | None = None
    stage_version: str | None = None
    manager_version: str | None = None
    rag_version: str | None = None
    promotion_role: str = "production"
    promotion_policy_status: str | None = None
    manifest_version: int | None = None
    manifest_path: str | None = None
    literal_lines: int | None = None
    return_code: int | None = None
    promotion_outcome: str | None = None
    commit_hash: str | None = None
    manual: bool = field(default=False)
    targets: list[str] | None = None
    batch_file: str | None = None
    auto_stage: bool | None = None
    auto_stage5_batch: bool | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        extra = data.pop("extra", None)
        if extra:
            clean_extra = {k: v for k, v in extra.items() if v is not None}
            if clean_extra:
                data["extra"] = clean_extra
        return {k: v for k, v in data.items() if v is not None}


def append_trace(entry: PromotionTraceEntry) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        json.dump(entry.to_dict(), fh, ensure_ascii=False)
        fh.write("\n")
