"""Structured action audit log for the control plane.

Writes one JSON line per action invocation to actions_log_path. Caller
identity (IP, tier3 state) is included in every entry so the audit
view can correlate operator → action → outcome.

Distinct from Vault's audit log (`/vault/logs/audit.log`). The Vault
audit log captures *Vault* operations; this log captures *control-
plane* operations. Both feed the unified audit search view.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings

log = logging.getLogger(__name__)
_lock = threading.Lock()
_path = Path(settings.actions_log_path)


def _ensure_dir() -> None:
    _path.parent.mkdir(parents=True, exist_ok=True)


def emit(
    *,
    action: str,
    tier: int,
    outcome: str,
    actor_ip: str,
    tier3_active: bool,
    detail: dict[str, Any] | None = None,
) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "tier": tier,
        "outcome": outcome,
        "actor_ip": actor_ip,
        "tier3_active": tier3_active,
        "detail": detail or {},
    }
    line = json.dumps(record, separators=(",", ":")) + "\n"
    try:
        with _lock:
            _ensure_dir()
            with _path.open("a", encoding="utf-8") as fh:
                fh.write(line)
    except OSError:
        log.exception("action audit log write failed")
