from typing import Any


def generalize(
    abstraction: dict[str, Any],
    invariant: dict[str, Any],
    generalization_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(abstraction, dict)
        or not isinstance(invariant, dict)
        or not isinstance(generalization_config, dict)
    ):
        return {
            "generalization_status": "invalid_input",
            "generalization_phase": None,
            "generalization_scope": None,
        }

    abstraction_ok = abstraction.get("abstraction_status") == "built"
    invariant_ok = invariant.get("invariant_status") == "detected"

    if abstraction_ok and invariant_ok:
        return {
            "generalization_status": "generalized",
            "generalization_phase": abstraction.get("abstraction_phase"),
            "generalization_scope": generalization_config.get("scope", "cross_phase"),
        }

    if not abstraction_ok:
        return {
            "generalization_status": "no_abstraction",
            "generalization_phase": None,
            "generalization_scope": None,
        }

    return {
        "generalization_status": "invalid_input",
        "generalization_phase": None,
        "generalization_scope": None,
    }
