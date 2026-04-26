#!/usr/bin/env python3
"""Background aider worker — claims tasks from the execution queue and runs aider at 2 AM."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_REPO = Path(__file__).parent.parent
_MAX_TASKS_PER_RUN = int(os.environ.get("AIDER_WORKER_MAX_TASKS", "5"))
_AIDER_MODEL = os.environ.get("AIDER_WORKER_MODEL", "ollama/qwen2.5-coder:14b")
_AIDER_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434")
_RUN_HOUR = int(os.environ.get("AIDER_WORKER_HOUR", "2"))   # 2 AM local time

# Status exposed to dashboard
_status: dict = {
    "running": False,
    "last_run_at": None,
    "last_run_tasks": 0,
    "last_run_errors": 0,
    "next_run_at": None,
    "aider_available": False,
}
_status_lock = threading.Lock()


def _update_status(**kw) -> None:
    with _status_lock:
        _status.update(kw)


def get_status() -> dict:
    with _status_lock:
        return dict(_status)


def _seconds_until_next_run() -> float:
    now = datetime.now()
    next_run = now.replace(hour=_RUN_HOUR, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run.replace(day=next_run.day + 1)
    return (next_run - now).total_seconds()


def _aider_available() -> bool:
    return shutil.which("aider") is not None


def _run_aider_on_task(task: dict) -> tuple[bool, str]:
    """Run aider against a single task. Returns (success, message)."""
    title       = task.get("title", "unknown task")
    description = task.get("description", "")
    target_files: list = task.get("target_files", [])

    message = f"{title}\n\n{description}" if description else title

    cmd = [
        "aider",
        "--model", _AIDER_MODEL,
        "--openai-api-base", _AIDER_API_BASE,
        "--no-auto-commits",
        "--yes",
        "--message", message,
    ]
    for f in target_files:
        full = _REPO / f
        if full.exists():
            cmd.append(str(full))

    log.info("aider_worker: running aider for task %s: %s", task.get("id", "?"), title)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(_REPO),
            capture_output=True,
            text=True,
            timeout=600,  # 10-minute hard cap per task
        )
        if result.returncode == 0:
            return True, result.stdout[-500:] if result.stdout else "ok"
        return False, (result.stderr or result.stdout or "")[-500:]
    except subprocess.TimeoutExpired:
        return False, "aider timed out (600s)"
    except Exception as exc:
        return False, str(exc)


def _execute_run() -> None:
    """Claim up to _MAX_TASKS_PER_RUN tasks and run aider on each."""
    from framework.execution_queue import get_queue

    _update_status(running=True, last_run_at=datetime.now().isoformat())
    log.info("aider_worker: starting scheduled run (max %d tasks)", _MAX_TASKS_PER_RUN)

    q = get_queue()
    completed = 0
    errors = 0

    for _ in range(_MAX_TASKS_PER_RUN):
        task = q.claim_next_task(engine="aider")
        if task is None:
            log.info("aider_worker: no more pending tasks")
            break

        task_id = task["id"]
        try:
            success, msg = _run_aider_on_task(task)
            q.complete_task(
                task_id,
                success=success,
                result={"output": msg} if success else None,
                error=msg if not success else None,
            )
            if success:
                completed += 1
            else:
                errors += 1
            log.info("aider_worker: task %s %s", task_id, "done" if success else f"failed: {msg[:80]}")
        except Exception as exc:
            errors += 1
            q.complete_task(task_id, success=False, error=str(exc))
            log.exception("aider_worker: unexpected error on task %s", task_id)

    _update_status(
        running=False,
        last_run_tasks=completed,
        last_run_errors=errors,
        next_run_at=(datetime.now().replace(
            hour=_RUN_HOUR, minute=0, second=0, microsecond=0
        ).isoformat()),
    )
    log.info("aider_worker: run complete — %d done, %d errors", completed, errors)


class AiderWorker:
    """Daemon thread that wakes at _RUN_HOUR each day and processes the queue."""

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        available = _aider_available()
        _update_status(aider_available=available)
        if not available:
            log.warning("aider_worker: aider not found on PATH — worker will not run tasks")
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="aider-worker", daemon=True)
        self._thread.start()
        log.info("aider_worker: started (runs daily at %02d:00, aider=%s)", _RUN_HOUR, available)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            secs = _seconds_until_next_run()
            _update_status(next_run_at=(
                datetime.now().replace(
                    hour=_RUN_HOUR, minute=0, second=0, microsecond=0
                ).isoformat()
            ))
            log.info("aider_worker: sleeping %.0fs until next run at %02d:00", secs, _RUN_HOUR)
            # Sleep in 60s chunks so stop() is responsive
            deadline = time.monotonic() + secs
            while time.monotonic() < deadline and not self._stop.is_set():
                time.sleep(min(60, deadline - time.monotonic()))
            if self._stop.is_set():
                break
            if _aider_available():
                try:
                    _execute_run()
                except Exception:
                    log.exception("aider_worker: _execute_run raised unexpectedly")
            else:
                log.warning("aider_worker: aider not available, skipping run")

    def trigger_now(self) -> str:
        """Manually trigger a run in a fire-and-forget thread. Returns status message."""
        if _status.get("running"):
            return "already running"
        if not _aider_available():
            return "aider not found on PATH"
        t = threading.Thread(target=_execute_run, name="aider-manual", daemon=True)
        t.start()
        return "started"


# ── Module-level singleton ────────────────────────────────────────────────────

_worker: Optional[AiderWorker] = None
_worker_lock = threading.Lock()


def get_worker() -> AiderWorker:
    global _worker
    if _worker is None:
        with _worker_lock:
            if _worker is None:
                _worker = AiderWorker()
    return _worker


# ── CLI convenience ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(json.dumps(get_status(), indent=2))
    elif cmd == "run-now":
        log.info("Triggering immediate run…")
        _execute_run()
        print(json.dumps(get_status(), indent=2))
    elif cmd == "daemon":
        w = get_worker()
        w.start()
        log.info("Daemon running. Ctrl-C to stop.")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            w.stop()
    else:
        print(f"Usage: {sys.argv[0]} [status|run-now|daemon]")
