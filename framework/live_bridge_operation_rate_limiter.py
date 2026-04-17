from typing import Any

def apply_rate_limit(inspector: dict[str, Any], limits: dict[str, Any], window_count: int) -> dict[str, Any]:
    if not isinstance(inspector, dict) or not isinstance(limits, dict) or not isinstance(window_count, int):
        return {"rate_limit_status": "invalid_input", "window_remaining": 0, "rate_tick": 0}
    if window_count < 0:
        return {"rate_limit_status": "invalid_input", "window_remaining": 0, "rate_tick": 0}
    max_per_window = limits.get("max_per_window", 10) if isinstance(limits, dict) else 10
    insp_ok = inspector.get("inspector_status") == "inspected"
    if not insp_ok:
        return {"rate_limit_status": "no_inspector", "window_remaining": 0, "rate_tick": limits.get("tick", 0)}
    if window_count >= max_per_window:
        return {"rate_limit_status": "limited", "window_remaining": 0, "rate_tick": limits.get("tick", 0)}
    return {"rate_limit_status": "allowed", "window_remaining": max_per_window - window_count, "rate_tick": limits.get("tick", 0)}
