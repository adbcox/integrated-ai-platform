from typing import Any

def watch_timeout(tracking: dict[str, Any], clock: dict[str, Any], watchdog_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tracking, dict) or not isinstance(clock, dict) or not isinstance(watchdog_config, dict):
        return {"watchdog_status": "invalid_input", "watched_operation_id": None, "elapsed_seconds": 0}
    t_ok = tracking.get("execution_tracking_status") == "tracking"
    if not t_ok:
        return {"watchdog_status": "not_tracking", "watched_operation_id": None, "elapsed_seconds": 0}
    now = int(clock.get("now", 0)) if isinstance(clock, dict) else 0
    started_at = int(clock.get("started_at", 0)) if isinstance(clock, dict) else 0
    elapsed = now - started_at
    timeout_s = int(watchdog_config.get("timeout_s", 30)) if isinstance(watchdog_config, dict) else 30
    if elapsed < 0:
        return {"watchdog_status": "invalid_input", "watched_operation_id": None, "elapsed_seconds": 0}
    if elapsed >= timeout_s:
        return {"watchdog_status": "timed_out", "watched_operation_id": tracking.get("tracked_operation_id"), "elapsed_seconds": elapsed}
    return {"watchdog_status": "ok", "watched_operation_id": tracking.get("tracked_operation_id"), "elapsed_seconds": elapsed}
