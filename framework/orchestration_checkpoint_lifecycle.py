from typing import Any


def transition_checkpoint_state(
    checkpoint: dict[str, Any],
    target_state: str,
) -> dict[str, Any]:
    valid_states = {"open", "committed", "expired", "recovered", "invalid"}
    allowed = {
        "open": {"committed", "expired", "invalid"},
        "committed": {"recovered", "expired"},
        "expired": {"recovered"},
        "recovered": {"committed"},
        "invalid": set(),
    }

    if not isinstance(checkpoint, dict) or target_state not in valid_states:
        return {
            "transition_valid": False,
            "prior_state": "open",
            "current_state": "open",
            "transition_allowed": False,
            "lifecycle_status": "invalid_input",
        }

    prior_state = checkpoint.get("lifecycle_state", "open")
    if prior_state not in valid_states:
        prior_state = "open"

    transition_allowed = target_state in allowed.get(prior_state, set())

    if transition_allowed:
        return {
            "transition_valid": True,
            "prior_state": prior_state,
            "current_state": target_state,
            "transition_allowed": True,
            "lifecycle_status": "transitioned",
        }

    return {
        "transition_valid": True,
        "prior_state": prior_state,
        "current_state": prior_state,
        "transition_allowed": False,
        "lifecycle_status": "rejected",
    }


def summarize_checkpoint_lifecycle(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("transition_valid") is not True:
        return {
            "summary_valid": False,
            "current_state": "unknown",
            "lifecycle_status": "invalid_input",
        }

    return {
        "summary_valid": True,
        "current_state": result.get("current_state", "unknown"),
        "lifecycle_status": result.get("lifecycle_status", "invalid_input"),
    }
