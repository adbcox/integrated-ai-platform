"""Append-only audit log for security-relevant dashboard operations."""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT  = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
AUDIT_PATH  = _REPO_ROOT / "artifacts" / "audit.jsonl"
_lock       = threading.Lock()

ACTION_LABELS = {
    "executor_started":    "Executor started",
    "executor_stopped":    "Executor stopped",
    "training_started":    "Training initiated",
    "training_stopped":    "Training stopped",
    "config_changed":      "Config modified",
    "queue_item_removed":  "Queue item removed",
    "rclone_forced":       "Manual rclone sync triggered",
    "missing_search":      "Missing-content search triggered",
    "model_deployed":      "Model deployed",
    "circuit_reset":       "Circuit breaker reset",
}


def log(
    action: str,
    resource: str = "",
    result: str = "ok",
    user_ip: str = "",
    detail: str = "",
) -> None:
    """Append one audit event. Never raises — audit failures must not break requests."""
    event = {
        "ts":       datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "action":   action,
        "resource": resource,
        "result":   result,
        "user_ip":  user_ip or "",
        "detail":   (detail or "")[:200],
        "label":    ACTION_LABELS.get(action, action),
    }
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with AUDIT_PATH.open("a") as f:
                f.write(json.dumps(event) + "\n")
    except Exception:
        pass


def tail(limit: int = 100) -> list[dict]:
    """Return the most recent `limit` events, newest first."""
    if not AUDIT_PATH.exists():
        return []
    try:
        with _lock:
            lines = AUDIT_PATH.read_text().splitlines()
        events = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
        return list(reversed(events[-limit:]))
    except Exception:
        return []


def stats() -> dict:
    """Return summary counts by action for the last 24 hours."""
    from collections import Counter
    cutoff = datetime.now(timezone.utc).timestamp() - 86400
    events = tail(1000)
    counts: Counter = Counter()
    for ev in events:
        try:
            ts = datetime.fromisoformat(ev["ts"]).timestamp()
            if ts >= cutoff:
                counts[ev["action"]] += 1
        except Exception:
            pass
    return dict(counts)
