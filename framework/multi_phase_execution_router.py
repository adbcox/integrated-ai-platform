from typing import Any

def route_execution_request(request: dict, coordinator: dict, materialization: dict) -> dict:
    if not isinstance(request, dict) or not isinstance(coordinator, dict) or not isinstance(materialization, dict):
        return {"routing_status": "invalid_input"}
    
    routing_allowed = coordinator.get("coordinator_status") == "initialized" and materialization.get("materialization_status") == "ready"
    
    if not routing_allowed:
        return {"routing_status": "not_ready"}
    
    operation = request.get("operation")
    
    if not operation:
        return {"routing_status": "invalid_input"}
    
    phase_id = coordinator.get("phase_id")
    request_phase_id = request.get("phase_id", "")
    
    if request_phase_id != phase_id:
        return {"routing_status": "phase_mismatch"}
    
    return {
        "routing_status": "routed",
        "routed_to": phase_id,
        "operation": operation
    }
