from typing import Any

def monitor_phase_health(cp: dict, routing_results: list, thresholds: dict) -> dict:
    if not isinstance(cp, dict):
        return {"health_status": "invalid_input"}
    
    phase_healthy = cp.get("control_plane_status") == "operational"
    
    if not phase_healthy:
        return {
            "health_status": "critical",
            "failed_routing_count": 0,
            "phase_id": cp.get("active_phase")
        }
    
    failed_count = sum(1 for r in routing_results if r.get("routing_status") != "routed") if isinstance(routing_results, list) else 0
    max_failures = thresholds.get("max_failures", 0) if isinstance(thresholds, dict) else 0
    
    if failed_count > max_failures:
        return {
            "health_status": "degraded",
            "failed_routing_count": failed_count,
            "phase_id": cp.get("active_phase")
        }
    
    return {
        "health_status": "healthy",
        "failed_routing_count": failed_count,
        "phase_id": cp.get("active_phase")
    }
