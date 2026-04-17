from typing import Any

def track_phase_transition(tracker: dict, from_phase: str, to_phase: str, propagation: dict) -> dict:
    if not isinstance(tracker, dict) or not isinstance(propagation, dict):
        return {"tracker_status": "invalid_input"}
    
    propagation_status = propagation.get("propagation_status")
    
    if propagation_status != "propagated":
        return {"tracker_status": "invalid_input"}
    
    if not isinstance(from_phase, str) or not from_phase or not isinstance(to_phase, str) or not to_phase:
        return {"tracker_status": "ordering_error"}
    
    if from_phase == to_phase:
        return {"tracker_status": "ordering_error"}
    
    return {
        "tracker_status": "recorded",
        "transition_id": f"{from_phase}->{to_phase}",
        "recorded_at": "now"
    }
