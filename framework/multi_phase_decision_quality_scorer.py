from typing import Any


def score_decision_quality(
    reward: dict[str, Any],
    confidence_scorer: dict[str, Any],
    quality_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(reward, dict)
        or not isinstance(confidence_scorer, dict)
        or not isinstance(quality_config, dict)
    ):
        return {
            "quality_status": "invalid_input",
            "quality_score": 0.0,
            "quality_phase": None,
            "decision_assessment": "none",
        }

    reward_ok = reward.get("reward_status") == "calculated"
    scored_ok = confidence_scorer.get("scoring_status") == "scored"
    top_score = confidence_scorer.get("top_score", 0.0) if scored_ok else 0.0
    reward_val = reward.get("reward_value", 0.0) if reward_ok else 0.0
    quality = top_score * reward_val if (reward_ok and scored_ok) else 0.0

    if reward_ok and scored_ok:
        assessment = "high" if quality >= 0.5 else "low"
        return {
            "quality_status": "scored",
            "quality_score": quality,
            "quality_phase": reward.get("reward_phase"),
            "decision_assessment": assessment,
        }

    if not reward_ok:
        return {
            "quality_status": "no_reward",
            "quality_score": 0.0,
            "quality_phase": None,
            "decision_assessment": "none",
        }

    return {
        "quality_status": "invalid_input",
        "quality_score": 0.0,
        "quality_phase": None,
        "decision_assessment": "none",
    }
