from typing import Any

def initialize_coordinator(seed_result: dict, config: dict) -> dict:
    if not isinstance(seed_result, dict) or not isinstance(config, dict):
        return {"coordinator_status": "invalid_input"}
    
    seed_ready = seed_result.get("seed_ready", False)
    seed_payload = seed_result.get("seed_payload")
    
    if not seed_ready:
        return {"coordinator_status": "seed_not_ready"}
    
    if seed_payload is None or not isinstance(seed_payload, dict):
        return {"coordinator_status": "invalid_input"}
    
    phase_id = seed_payload.get("target_phase", "phase-5")
    approved_releases = seed_payload.get("approved_releases", 0)
    source_terminal_status = seed_payload.get("terminal_status", "")
    
    return {
        "coordinator_status": "initialized",
        "phase_id": phase_id,
        "approved_releases": approved_releases,
        "source_terminal_status": source_terminal_status
    }
