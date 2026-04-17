from typing import Any


def evaluate_lookahead(
    milestone: dict[str, Any],
    counterfactual: dict[str, Any],
    lookahead_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(milestone, dict)
        or not isinstance(counterfactual, dict)
        or not isinstance(lookahead_config, dict)
    ):
        return {
            "lookahead_status": "invalid_input",
            "lookahead_phase": None,
            "lookahead_horizon": 0,
        }

    milestone_ok = milestone.get("milestone_status") == "scheduled"
    counterfactual_ok = counterfactual.get("counterfactual_status") == "evaluated"

    if milestone_ok and counterfactual_ok:
        return {
            "lookahead_status": "evaluated",
            "lookahead_phase": milestone.get("milestone_phase"),
            "lookahead_horizon": lookahead_config.get("horizon", 3),
        }

    if not milestone_ok:
        return {
            "lookahead_status": "no_milestone",
            "lookahead_phase": None,
            "lookahead_horizon": 0,
        }

    return {
        "lookahead_status": "invalid_input",
        "lookahead_phase": None,
        "lookahead_horizon": 0,
    }
