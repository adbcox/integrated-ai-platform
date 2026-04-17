from typing import Any


def break_tie(
    arbitration: dict[str, Any],
    confidence_scorer: dict[str, Any],
    tiebreak_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(arbitration, dict)
        or not isinstance(confidence_scorer, dict)
        or not isinstance(tiebreak_policy, dict)
    ):
        return {
            "tiebreak_status": "invalid_input",
            "resolved_phase": None,
            "winning_score": 0.0,
        }

    arb_ok = arbitration.get("arbitration_status") == "arbitrated"
    scored_ok = confidence_scorer.get("scoring_status") == "scored"
    threshold = float(tiebreak_policy.get("threshold", 0.5))
    top_score = float(confidence_scorer.get("top_score", 0.0))
    has_clear_winner = top_score >= threshold

    if arb_ok and scored_ok and has_clear_winner:
        return {
            "tiebreak_status": "resolved",
            "resolved_phase": arbitration.get("arbitrated_phase"),
            "winning_score": top_score,
        }

    if arb_ok and scored_ok and not has_clear_winner:
        return {
            "tiebreak_status": "unresolvable",
            "resolved_phase": None,
            "winning_score": 0.0,
        }

    if not arb_ok:
        return {"tiebreak_status": "no_tie", "resolved_phase": None, "winning_score": 0.0}

    return {
        "tiebreak_status": "invalid_input",
        "resolved_phase": None,
        "winning_score": 0.0,
    }
