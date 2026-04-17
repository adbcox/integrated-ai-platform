from typing import Any

def build_control_plane(coord: dict, tracker: dict, mat: dict, log: dict) -> dict:
    if not isinstance(coord, dict) or not isinstance(tracker, dict) or not isinstance(mat, dict) or not isinstance(log, dict):
        return {"control_plane_status": "invalid_input"}
    
    all_operational = coord.get("coordinator_status") == "initialized" and mat.get("materialization_status") == "ready"
    
    if not all_operational:
        return {"control_plane_status": "offline"}
    
    tracker_status = tracker.get("tracker_status")
    
    if tracker_status != "recorded":
        return {"control_plane_status": "degraded"}
    
    active_phase = coord.get("phase_id")
    
    return {
        "control_plane_status": "operational",
        "active_phase": active_phase,
        "component_count": 4
    }
