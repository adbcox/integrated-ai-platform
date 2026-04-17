from typing import Any


def negotiate_priority(
    selection: dict[str, Any],
    existing_priorities: dict[str, Any],
    negotiation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(selection, dict)
        or not isinstance(existing_priorities, dict)
        or not isinstance(negotiation_config, dict)
    ):
        return {
            "negotiation_status": "invalid_input",
            "negotiated_action": None,
            "negotiated_phase": None,
            "final_confidence": 0.0,
        }

    selection_ok = selection.get("selection_status") == "selected"
    current_conf = float(selection.get("confidence", 0.0))
    has_conflict = any(
        v > current_conf
        for v in existing_priorities.values()
        if isinstance(v, (int, float))
    )

    if selection_ok and not has_conflict:
        return {
            "negotiation_status": "negotiated",
            "negotiated_action": selection.get("selected_action"),
            "negotiated_phase": selection.get("selected_phase"),
            "final_confidence": current_conf,
        }

    if selection_ok and has_conflict:
        return {
            "negotiation_status": "conflict",
            "negotiated_action": None,
            "negotiated_phase": None,
            "final_confidence": 0.0,
        }

    return {
        "negotiation_status": "no_selection",
        "negotiated_action": None,
        "negotiated_phase": None,
        "final_confidence": 0.0,
    }
