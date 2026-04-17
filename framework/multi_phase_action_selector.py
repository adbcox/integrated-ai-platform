from typing import Any


def select_phase_action(
    scored_candidates: dict[str, Any],
    policy_rules: dict[str, Any],
    selection_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(scored_candidates, dict)
        or not isinstance(policy_rules, dict)
        or not isinstance(selection_config, dict)
    ):
        return {
            "selection_status": "invalid_input",
            "selected_action": None,
            "selected_phase": None,
            "confidence": 0.0,
        }

    scored_ok = scored_candidates.get("scoring_status") == "scored"
    rules_nonempty = len(policy_rules) > 0

    if scored_ok and rules_nonempty:
        return {
            "selection_status": "selected",
            "selected_action": list(policy_rules.keys())[0],
            "selected_phase": scored_candidates.get("scored_phase"),
            "confidence": float(scored_candidates.get("top_score", 0.0)),
        }

    if not scored_ok:
        return {
            "selection_status": "no_scoring",
            "selected_action": None,
            "selected_phase": None,
            "confidence": 0.0,
        }

    return {
        "selection_status": "policy_blocked",
        "selected_action": None,
        "selected_phase": None,
        "confidence": 0.0,
    }
