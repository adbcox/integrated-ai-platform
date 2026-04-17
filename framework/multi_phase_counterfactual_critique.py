from typing import Any


def critique_counterfactual(
    critique_extraction: dict[str, Any],
    counterfactual_evaluation: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(critique_extraction, dict)
        or not isinstance(counterfactual_evaluation, dict)
        or not isinstance(config, dict)
    ):
        return {
            "cf_critique_status": "invalid_input",
            "cf_critique_phase": None,
            "cf_score": None,
        }

    ce_ok = critique_extraction.get("critique_status") == "extracted"
    cfe_ok = counterfactual_evaluation.get("counterfactual_status") == "evaluated"
    all_ok = ce_ok and cfe_ok

    if all_ok:
        return {
            "cf_critique_status": "synthesized",
            "cf_critique_phase": critique_extraction.get("critique_phase"),
            "cf_score": counterfactual_evaluation.get("projected_outcome"),
        }

    return {
        "cf_critique_status": "failed",
        "cf_critique_phase": None,
        "cf_score": None,
    }
