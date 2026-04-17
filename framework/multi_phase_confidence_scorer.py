from typing import Any


def score_action_confidence(
    candidates: dict[str, Any],
    profile: dict[str, Any],
    trend: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(candidates, dict)
        or not isinstance(profile, dict)
        or not isinstance(trend, dict)
    ):
        return {
            "scoring_status": "invalid_input",
            "top_score": 0.0,
            "scored_count": 0,
            "scored_phase": None,
        }

    candidates_ok = candidates.get("candidate_status") == "generated"
    profile_ok = profile.get("profile_status") == "profiled"
    trend_ok = trend.get("trend_status") == "analyzed"

    if candidates_ok and profile_ok and trend_ok:
        return {
            "scoring_status": "scored",
            "top_score": 0.85,
            "scored_count": int(candidates.get("candidate_count", 0)),
            "scored_phase": candidates.get("candidate_phase"),
        }

    if not candidates_ok:
        return {
            "scoring_status": "no_candidates",
            "top_score": 0.0,
            "scored_count": 0,
            "scored_phase": None,
        }

    return {
        "scoring_status": "invalid_input",
        "top_score": 0.0,
        "scored_count": 0,
        "scored_phase": None,
    }
