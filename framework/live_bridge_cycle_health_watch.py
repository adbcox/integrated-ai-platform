from typing import Any

def watch_cycle_health(bridge_health: dict[str, Any], backpressure: dict[str, Any], watch_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_health, dict) or not isinstance(backpressure, dict) or not isinstance(watch_config, dict):
        return {"cycle_health_watch_status": "invalid_input", "cycle_health_env_id": None, "observed_pressure": "unknown"}
    bh_healthy = bridge_health.get("bridge_health_status") == "healthy"
    bp_normal = backpressure.get("backpressure_status") == "normal"
    if bh_healthy and bp_normal:
        return {"cycle_health_watch_status": "green", "cycle_health_env_id": bridge_health.get("health_env_id"), "observed_pressure": "low"}
    if bh_healthy and not bp_normal:
        return {"cycle_health_watch_status": "yellow", "cycle_health_env_id": None, "observed_pressure": backpressure.get("pressure_level", "unknown")}
    return {"cycle_health_watch_status": "red", "cycle_health_env_id": None, "observed_pressure": backpressure.get("pressure_level", "unknown")}
