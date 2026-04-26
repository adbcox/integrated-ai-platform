"""Append-only log for self-healing daemon actions."""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
HEAL_LOG   = _REPO_ROOT / "artifacts" / "selfheal.jsonl"
_lock      = threading.Lock()


def log_check(service: str, issue_count: int, fix_count: int, duration_s: float) -> None:
    _append({
        "type":        "check",
        "ts":          _now(),
        "service":     service,
        "issue_count": issue_count,
        "fix_count":   fix_count,
        "duration_s":  round(duration_s, 2),
    })


def log_fix(service: str, action: str, detail: str, ok: bool, error: str = "") -> None:
    _append({
        "type":    "fix",
        "ts":      _now(),
        "service": service,
        "action":  action,
        "detail":  detail[:200],
        "ok":      ok,
        "error":   error[:120],
    })


def log_issue(service: str, severity: str, message: str, fixable: bool) -> None:
    _append({
        "type":     "issue",
        "ts":       _now(),
        "service":  service,
        "severity": severity,
        "message":  message[:200],
        "fixable":  fixable,
    })


def tail(limit: int = 200) -> list[dict]:
    if not HEAL_LOG.exists():
        return []
    try:
        with _lock:
            lines = HEAL_LOG.read_text().splitlines()
        out = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
        return list(reversed(out[-limit:]))
    except Exception:
        return []


def recent_fixes(limit: int = 20) -> list[dict]:
    return [e for e in tail(200) if e.get("type") == "fix"][:limit]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append(event: dict) -> None:
    try:
        HEAL_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with HEAL_LOG.open("a") as f:
                f.write(json.dumps(event) + "\n")
    except Exception:
        pass
