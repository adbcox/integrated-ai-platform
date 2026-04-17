from typing import Any


def score_promotion_readiness(
    benchmark_score: dict[str, Any],
    robustness_score: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_score, dict)
        or not isinstance(robustness_score, dict)
        or not isinstance(config, dict)
    ):
        return {
            "promotion_readiness_status": "invalid_input",
            "promotion_score": None,
            "promotion_phase": None,
        }

    bs_ok = benchmark_score.get("benchmark_score_status") == "scored"
    rs_ok = robustness_score.get("robustness_status") == "scored"
    all_ok = bs_ok and rs_ok

    if all_ok:
        return {
            "promotion_readiness_status": "ready",
            "promotion_score": benchmark_score.get("benchmark_score"),
            "promotion_phase": benchmark_score.get("score_phase"),
        }

    return {
        "promotion_readiness_status": "failed",
        "promotion_score": None,
        "promotion_phase": None,
    }
