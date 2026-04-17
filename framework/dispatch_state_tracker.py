from typing import Any

def track_dispatch_state_transition(
    job_id: str,
    from_state: str,
    to_state: str,
) -> dict[str, Any]:
    valid_transitions = {
        "queued": ["scheduled"],
        "scheduled": ["dispatching"],
        "dispatching": ["dispatched"],
        "dispatched": [],
    }
    allowed_states = valid_transitions.get(from_state, [])
    state_valid = to_state in allowed_states or from_state == "unknown"
    return {
        "job_id": job_id,
        "from_state": from_state,
        "to_state": to_state,
        "state_valid": state_valid,
        "state_chain": [from_state, to_state],
    }
