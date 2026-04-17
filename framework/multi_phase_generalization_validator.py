from typing import Any


def validate_generalization(
    generalization: dict[str, Any],
    invariant: dict[str, Any],
    gen_validation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization, dict)
        or not isinstance(invariant, dict)
        or not isinstance(gen_validation_config, dict)
    ):
        return {
            "gen_validation_status": "invalid_input",
            "validated_phase": None,
            "generalization_complete": False,
        }

    g_ok = generalization.get("generalization_status") == "generalized"
    i_ok = invariant.get("invariant_status") == "detected"
    all_ok = g_ok and i_ok
    any_ok = g_ok or i_ok

    if all_ok:
        return {
            "gen_validation_status": "valid",
            "validated_phase": generalization.get("generalization_phase"),
            "generalization_complete": True,
        }

    if any_ok:
        return {
            "gen_validation_status": "partial",
            "validated_phase": None,
            "generalization_complete": False,
        }

    return {
        "gen_validation_status": "failed",
        "validated_phase": None,
        "generalization_complete": False,
    }
