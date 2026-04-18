from typing import Any
def watch_dispatch_timeout(watchdog_input):
    if not isinstance(watchdog_input, dict): return {"op_dispatch_timeout_watch_status": "invalid"}
    if watchdog_input.get("op_dispatch_track_status") != "tracked": return {"op_dispatch_timeout_watch_status": "invalid"}
    if "timeout_seconds" not in watchdog_input or watchdog_input.get("timeout_seconds", 0) <= 0: return {"op_dispatch_timeout_watch_status": "invalid"}
    return {"op_dispatch_timeout_watch_status": "monitored", "timeout_seconds": watchdog_input.get("timeout_seconds")}
