from typing import Any
def watch_session_timeout(watchdog):
    if not isinstance(watchdog, dict): return {"op_session_timeout_watch_status": "invalid"}
    if "timeout_seconds" not in watchdog: return {"op_session_timeout_watch_status": "invalid"}
    if watchdog.get("timeout_seconds", 0) <= 0: return {"op_session_timeout_watch_status": "invalid"}
    return {"op_session_timeout_watch_status": "monitored", "timeout_seconds": watchdog.get("timeout_seconds")}
