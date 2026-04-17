from typing import Any

def check_lifecycle_coherence(lifecycle_sequence: list[str]) -> dict[str, Any]:
    valid_transitions = {
        "accepted": ["queued"],
        "queued": ["dispatched"],
        "dispatched": ["running", "failed"],
        "running": ["completed", "failed", "retry_waiting"],
        "retry_waiting": ["queued"],
        "completed": [],
        "failed": ["escalated"],
        "escalated": [],
        "canceled": [],
    }
    if not lifecycle_sequence:
        return {"valid": True, "errors": []}
    errors = []
    for i in range(len(lifecycle_sequence) - 1):
        current = lifecycle_sequence[i]
        next_state = lifecycle_sequence[i + 1]
        allowed = valid_transitions.get(current, [])
        if next_state not in allowed:
            errors.append("Invalid transition {} -> {}".format(current, next_state))
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "sequence": lifecycle_sequence,
    }
