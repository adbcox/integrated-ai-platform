from typing import Any

KNOWN_BUS_EVENTS = {"phase_transition", "state_change", "health_alert", "resource_update", "audit_event", "coordination_complete", "routing_complete", "checkpoint_bridged"}

def publish_phase_event(bus: dict, event_type: str, source_phase: str, payload: dict) -> dict:
    if not isinstance(bus, dict) or not isinstance(event_type, str) or not isinstance(source_phase, str) or not isinstance(payload, dict):
        return {"publish_status": "invalid_input"}
    
    if event_type not in KNOWN_BUS_EVENTS:
        return {"publish_status": "unknown_event_type"}
    
    return {
        "publish_status": "published",
        "message_count": bus.get("message_count", 0) + 1,
        "last_event": event_type
    }
