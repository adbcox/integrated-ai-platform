"""Trigger-file protocol with nonce + timestamp anti-replay.

Per Block 2.5 D8: control-plane never holds elevated credentials
(root vault token, host docker exec). Operations that need them
(manual backup, regression probe, credential rotation) are dispatched
to a host-side launchd job via trigger files in a shared directory.

Protocol:
  1. control-plane writes:
       <trigger_dir>/<action>-<uuid>.json
     containing {"nonce": uuid, "timestamp": iso8601, "params": {...}}

  2. Host watcher (`iap-trigger-watcher.sh`) picks it up:
     - Validates timestamp within 30 s of now
     - Validates nonce is not in recent-nonce cache (replay defense)
     - Executes the corresponding /usr/local/bin/iap-<action>-trigger
     - Writes <trigger_dir>/results/<uuid>.json with the structured result
     - Atomic-deletes the input trigger file

  3. control-plane polls for the result file by uuid, reads it,
     deletes it, returns to caller. If no result within timeout,
     returns 504.

Trigger files are world-unreadable (0600); the trigger directory is
owned by the operator with the host watcher running under the same
account, so the docker container (writing as its own UID via volume
mount) and the host watcher share access through the volume.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import settings

log = logging.getLogger(__name__)

ALLOWED_ACTIONS = frozenset(
    {"backup-trigger", "regression-probe", "credential-rotate"}
)


class TriggerError(RuntimeError):
    pass


class TriggerTimeout(TriggerError):
    pass


class TriggerRejected(TriggerError):
    pass


def _trigger_dir() -> Path:
    p = Path(settings.trigger_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "results").mkdir(parents=True, exist_ok=True)
    return p


async def dispatch(
    action: str,
    params: Optional[dict[str, Any]] = None,
    timeout_s: float = 600.0,
    poll_interval_s: float = 0.5,
) -> dict[str, Any]:
    """Write a trigger file and await the result. Returns the parsed
    result JSON. Raises TriggerTimeout if no result arrives within
    `timeout_s`. Raises TriggerRejected if the host watcher refused
    to execute (stale timestamp / replay / unknown action).
    """
    if action not in ALLOWED_ACTIONS:
        raise TriggerRejected(f"action {action!r} not in allowlist")

    nonce = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {"nonce": nonce, "timestamp": timestamp, "action": action,
               "params": params or {}}

    tdir = _trigger_dir()
    trigger_path = tdir / f"{action}-{nonce}.json"
    result_path = tdir / "results" / f"{nonce}.json"
    rejected_path = tdir / "results" / f"{nonce}.rejected.json"

    # Write atomically
    tmp = trigger_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.rename(trigger_path)

    log.info("dispatched trigger action=%s nonce=%s", action, nonce)

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if result_path.exists():
            data = json.loads(result_path.read_text(encoding="utf-8"))
            try:
                result_path.unlink()
            except FileNotFoundError:
                pass
            return data
        if rejected_path.exists():
            data = json.loads(rejected_path.read_text(encoding="utf-8"))
            try:
                rejected_path.unlink()
            except FileNotFoundError:
                pass
            raise TriggerRejected(data.get("reason", "rejected"))
        await asyncio.sleep(poll_interval_s)

    # Cleanup the unconsumed trigger file so the host doesn't
    # process it after we've given up.
    try:
        trigger_path.unlink()
    except FileNotFoundError:
        pass
    raise TriggerTimeout(f"no result for action={action} nonce={nonce}")
