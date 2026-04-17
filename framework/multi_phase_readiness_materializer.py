from typing import Any

def materialize_readiness(propagation: dict, coordinator: dict, dep_map: dict) -> dict:
    if not isinstance(propagation, dict) or not isinstance(coordinator, dict) or not isinstance(dep_map, dict):
        return {"materialization_status": "invalid_input"}
    
    propagation_status = propagation.get("propagation_status")
    coordinator_status = coordinator.get("coordinator_status")
    mapping_status = dep_map.get("mapping_status")
    
    if propagation_status != "propagated" or coordinator_status != "initialized" or mapping_status not in ("mapped", "partial"):
        return {"materialization_status": "not_ready"}
    
    ready_phase = coordinator.get("phase_id")
    materialized_operations = dep_map.get("resolved_operations", [])
    
    return {
        "materialization_status": "ready",
        "ready_phase": ready_phase,
        "materialized_operations": materialized_operations
    }
