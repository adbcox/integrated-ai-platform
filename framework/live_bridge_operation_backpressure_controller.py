from typing import Any

def apply_backpressure(inspector: dict[str, Any], bridge_health: dict[str, Any], pressure_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(inspector, dict) or not isinstance(bridge_health, dict) or not isinstance(pressure_config, dict):
        return {"backpressure_status": "invalid_input", "pressure_level": "low", "observed_depth": 0}
    depth = int(inspector.get("depth", 0)) if isinstance(inspector, dict) else 0
    max_depth = pressure_config.get("max_depth", 50) if isinstance(pressure_config, dict) else 50
    h_healthy = bridge_health.get("bridge_health_status") == "healthy"
    h_critical = bridge_health.get("bridge_health_status") == "critical"
    if h_critical:
        return {"backpressure_status": "critical", "pressure_level": "emergency", "observed_depth": depth}
    if h_healthy and depth >= max_depth:
        return {"backpressure_status": "applied", "pressure_level": "high", "observed_depth": depth}
    if h_healthy and depth < max_depth:
        return {"backpressure_status": "normal", "pressure_level": "low", "observed_depth": depth}
    return {"backpressure_status": "invalid_input", "pressure_level": "low", "observed_depth": depth}
