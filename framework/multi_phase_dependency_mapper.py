from typing import Any

def map_phase_dependencies(coordinator: dict, operations: list, prior_outputs: dict) -> dict:
    if not isinstance(coordinator, dict) or not isinstance(operations, list) or not isinstance(prior_outputs, dict):
        return {"mapping_status": "invalid_input"}
    
    coordinator_status = coordinator.get("coordinator_status")
    
    if coordinator_status != "initialized":
        return {"mapping_status": "invalid_input"}
    
    if len(operations) == 0:
        if len(prior_outputs) == 0:
            return {"mapping_status": "empty"}
        else:
            return {"mapping_status": "partial"}
    
    resolved_operations = [op for op in operations if isinstance(op, str)]
    
    return {
        "mapping_status": "mapped",
        "dependency_count": len(resolved_operations),
        "resolved_operations": resolved_operations
    }
