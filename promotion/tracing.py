"""Versioned trace schema for Manager-4 lane routing."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = REPO_ROOT / "artifacts" / "manager4"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
SCHEMA_VERSION = "trace-v1"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_commit_hash() -> Optional[str]:
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
    lane: str
    lane_label: str
    lane_status: str
    lane_reason: str
    stage: Optional[str] = None
    stage_version: Optional[str] = None
    manager_version: Optional[str] = None
    rag_version: Optional[str] = None
    promotion_role: str = "production"
    promotion_policy_status: Optional[str] = None
    manifest_version: Optional[int] = None
    manifest_path: Optional[str] = None
    literal_lines: Optional[int] = None
    return_code: Optional[int] = None
    promotion_outcome: Optional[str] = None
    commit_hash: Optional[str] = None
    manual: bool = field(default=False)
    targets: Optional[list[str]] = None
    batch_file: Optional[str] = None
    auto_stage: Optional[bool] = None
    auto_stage5_batch: Optional[bool] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = field(init=False, default=SCHEMA_VERSION)
    timestamp: str = field(default_factory=_utc_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        extra = data.pop("extra", None)
        if extra:
            clean_extra = {k: v for k, v in extra.items() if v is not None}
            if clean_extra:
                data["extra"] = clean_extra
        return {k: v for k, v in data.items() if v is not None}


def append_trace(entry: PromotionTraceEntry, trace_dir: Optional[Path] = None) -> None:
    target_dir = Path(trace_dir) if trace_dir is not None else TRACE_DIR
    target_file = target_dir / "traces.jsonl"
    target_dir.mkdir(parents=True, exist_ok=True)
    with target_file.open("a", encoding="utf-8") as fh:
        json.dump(entry.to_dict(), fh, ensure_ascii=False)
        fh.write("\n")
