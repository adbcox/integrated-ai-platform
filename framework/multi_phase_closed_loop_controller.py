from typing import Any


def control_closed_loop(
    diagnostic_tuning: dict[str, Any],
    adaptive_routing: dict[str, Any],
    loop_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(diagnostic_tuning, dict)
        or not isinstance(adaptive_routing, dict)
        or not isinstance(loop_config, dict)
    ):
        return {
            "loop_status": "invalid_input",
            "loop_phase": None,
            "loop_frequency": None,
        }

    diag_tuned = diagnostic_tuning.get("diagnostic_tuning_status") == "tuned"
    routing_ok = adaptive_routing.get("adaptive_routing_status") in (
        "adapted",
        "no_preemption",
    )

    if diag_tuned and routing_ok:
        return {
            "loop_status": "closed",
            "loop_phase": diagnostic_tuning.get("tuned_phase"),
            "loop_frequency": loop_config.get("frequency", "periodic"),
        }

    if (diag_tuned and not routing_ok) or (routing_ok and not diag_tuned):
        return {"loop_status": "open", "loop_phase": None, "loop_frequency": None}

    if not diag_tuned:
        return {"loop_status": "no_tuning", "loop_phase": None, "loop_frequency": None}

    return {
        "loop_status": "invalid_input",
        "loop_phase": None,
        "loop_frequency": None,
    }
