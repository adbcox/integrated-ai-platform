from typing import Any


def build_generalization_control_plane(
    generalization_validation: dict[str, Any],
    pattern_rollup: dict[str, Any],
    event_bus: dict[str, Any],
    cp_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization_validation, dict)
        or not isinstance(pattern_rollup, dict)
        or not isinstance(event_bus, dict)
        or not isinstance(cp_config, dict)
    ):
        return {
            "generalization_cp_status": "offline",
            "cp_phase": None,
            "message_count": 0,
        }

    gv_ok = generalization_validation.get("gen_validation_status") == "valid"
    pr_ok = pattern_rollup.get("pattern_rollup_status") == "rolled_up"
    msg_ok = event_bus.get("message_count", 0) >= 0

    if gv_ok and pr_ok and msg_ok:
        return {
            "generalization_cp_status": "operational",
            "cp_phase": generalization_validation.get("validated_phase"),
            "message_count": event_bus.get("message_count", 0),
        }

    if (gv_ok and pr_ok) or (gv_ok and msg_ok) or (pr_ok and msg_ok):
        return {
            "generalization_cp_status": "degraded",
            "cp_phase": None,
            "message_count": 0,
        }

    return {
        "generalization_cp_status": "offline",
        "cp_phase": None,
        "message_count": 0,
    }
