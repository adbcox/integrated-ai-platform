from typing import Any


def validate_propagation(
    propagation: dict[str, Any],
    curriculum: dict[str, Any],
    prop_validation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(propagation, dict)
        or not isinstance(curriculum, dict)
        or not isinstance(prop_validation_config, dict)
    ):
        return {
            "prop_validation_status": "invalid_input",
            "validated_phase": None,
            "propagation_complete": False,
        }

    p_ok = propagation.get("propagation_status") == "propagated"
    c_ok = curriculum.get("curriculum_status") == "shaped"
    all_ok = p_ok and c_ok
    any_ok = p_ok or c_ok

    if all_ok:
        return {
            "prop_validation_status": "valid",
            "validated_phase": propagation.get("propagated_phase"),
            "propagation_complete": True,
        }

    if any_ok:
        return {
            "prop_validation_status": "partial",
            "validated_phase": None,
            "propagation_complete": False,
        }

    return {
        "prop_validation_status": "failed",
        "validated_phase": None,
        "propagation_complete": False,
    }
