from typing import Any


def detect_capability_gaps(
    weakness_detector: dict[str, Any],
    benchmark_scorer: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(weakness_detector, dict)
        or not isinstance(benchmark_scorer, dict)
        or not isinstance(config, dict)
    ):
        return {
            "gap_status": "invalid_input",
            "gap_count": 0,
            "gap_phase": None,
        }

    wd_ok = weakness_detector.get("weakness_status") == "detected"
    bs_ok = benchmark_scorer.get("benchmark_score_status") == "scored"
    bs_score = benchmark_scorer.get("benchmark_score", 0)
    has_gaps = bs_score is not None and bs_score < 0.8

    if wd_ok and bs_ok:
        if has_gaps:
            return {
                "gap_status": "detected",
                "gap_count": weakness_detector.get("weakness_count", 0),
                "gap_phase": weakness_detector.get("weakness_phase"),
            }
        else:
            return {
                "gap_status": "none",
                "gap_count": 0,
                "gap_phase": weakness_detector.get("weakness_phase"),
            }

    return {
        "gap_status": "failed",
        "gap_count": 0,
        "gap_phase": None,
    }
