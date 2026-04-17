from typing import Any

def track_phase_resources(tracker: dict, phase_id: str, snapshot: dict) -> dict:
    if not isinstance(tracker, dict) or not isinstance(phase_id, str) or not isinstance(snapshot, dict):
        return {"tracker_status": "invalid_input"}
    
    if not phase_id:
        return {"tracker_status": "invalid_input"}
    
    is_new = phase_id not in tracker.get("phases", {})
    
    if is_new:
        return {
            "tracker_status": "added",
            "phase_count": len(tracker.get("phases", {})) + 1,
            "tracked_phase": phase_id
        }
    else:
        return {
            "tracker_status": "updated",
            "phase_count": len(tracker.get("phases", {})),
            "tracked_phase": phase_id
        }
