from typing import Any
def watch_terminal_health(watch_input):
    if not isinstance(watch_input, dict): return {"op_terminal_health_watch_status": "invalid"}
    if "health_id" not in watch_input: return {"op_terminal_health_watch_status": "invalid"}
    return {"op_terminal_health_watch_status": "watching", "health_id": watch_input.get("health_id")}
