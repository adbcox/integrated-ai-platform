from typing import Any


def calculate_reward(
    classification: dict[str, Any],
    counterfactual: dict[str, Any],
    reward_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(classification, dict)
        or not isinstance(counterfactual, dict)
        or not isinstance(reward_config, dict)
    ):
        return {
            "reward_status": "invalid_input",
            "reward_value": 0.0,
            "reward_phase": None,
            "counterfactual_outcome": 0,
        }

    cls_ok = classification.get("classification_status") in (
        "success",
        "partial_success",
        "failure",
    )
    cf_ok = counterfactual.get("counterfactual_status") == "evaluated"

    if classification.get("classification_status") == "success":
        base_reward = 1.0
    elif classification.get("classification_status") == "partial_success":
        base_reward = 0.5
    elif classification.get("classification_status") == "failure":
        base_reward = -1.0
    else:
        base_reward = 0.0

    if cls_ok and cf_ok:
        return {
            "reward_status": "calculated",
            "reward_value": base_reward,
            "reward_phase": classification.get("classified_phase"),
            "counterfactual_outcome": counterfactual.get("projected_outcome", 0),
        }

    if not cls_ok:
        return {
            "reward_status": "no_classification",
            "reward_value": 0.0,
            "reward_phase": None,
            "counterfactual_outcome": 0,
        }

    return {
        "reward_status": "invalid_input",
        "reward_value": 0.0,
        "reward_phase": None,
        "counterfactual_outcome": 0,
    }
