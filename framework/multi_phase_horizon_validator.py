from typing import Any


def validate_horizon(
    horizon_plan: dict[str, Any],
    lookahead: dict[str, Any],
    horizon_validation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(horizon_plan, dict)
        or not isinstance(lookahead, dict)
        or not isinstance(horizon_validation_config, dict)
    ):
        return {
            "horizon_validation_status": "invalid_input",
            "validated_phase": None,
            "horizon_complete": False,
        }

    hp_ok = horizon_plan.get("horizon_plan_status") == "planned"
    la_ok = lookahead.get("lookahead_status") == "evaluated"
    all_ok = hp_ok and la_ok
    any_ok = hp_ok or la_ok

    if all_ok:
        return {
            "horizon_validation_status": "valid",
            "validated_phase": horizon_plan.get("horizon_phase"),
            "horizon_complete": True,
        }

    if any_ok:
        return {
            "horizon_validation_status": "partial",
            "validated_phase": None,
            "horizon_complete": False,
        }

    return {
        "horizon_validation_status": "failed",
        "validated_phase": None,
        "horizon_complete": False,
    }
