from typing import Any

KNOWN_EVENT_TYPES = {"phase_initialized", "state_propagated", "transition_recorded", "dependencies_mapped", "readiness_materialized", "execution_routed", "health_checked", "resource_updated"}

def log_phase_event(log: dict, event_type: str, phase_id: str, data: dict) -> dict:
    if not isinstance(log, dict) or not isinstance(event_type, str) or not isinstance(phase_id, str) or not isinstance(data, dict):
        return {"log_status": "invalid_input"}
    
    if event_type not in KNOWN_EVENT_TYPES:
        return {"log_status": "unknown_event_type"}
    
    return {
        "log_status": "logged",
        "event_count": log.get("event_count", 0) + 1,
        "last_event_type": event_type
    }
