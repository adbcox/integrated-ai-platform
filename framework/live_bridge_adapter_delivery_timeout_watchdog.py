from typing import Any

def watch_delivery_timeout(tracking: Any, clock: Any, watchdog_config: Any) -> dict[str, Any]:
    if not isinstance(tracking, dict) or not isinstance(clock, dict):
        return {"delivery_timeout_watchdog_status": "timeout"}
    t_ok = tracking.get("delivery_tracking_status") == "tracking"
    if not t_ok:
        return {"delivery_timeout_watchdog_status": "timeout"}
    elapsed = clock.get("elapsed_seconds", 0)
    timeout_s = watchdog_config.get("timeout_seconds", 60) if isinstance(watchdog_config, dict) else 60
    if elapsed < timeout_s:
        return {
            "delivery_timeout_watchdog_status": "ok",
            "adapter_id": tracking.get("adapter_id"),
            "elapsed_seconds": elapsed,
        }
    return {"delivery_timeout_watchdog_status": "timeout", "elapsed_seconds": elapsed}
