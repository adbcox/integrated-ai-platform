from typing import Any


def report_benchmark(
    benchmark_scorer: dict[str, Any],
    promotion_readiness: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_scorer, dict)
        or not isinstance(promotion_readiness, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "benchmark_report_status": "invalid_input",
            "report_phase": None,
            "report_detail": None,
        }

    bs_ok = benchmark_scorer.get("benchmark_score_status") == "scored"
    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"
    all_ok = bs_ok and pr_ok

    if all_ok:
        return {
            "benchmark_report_status": "complete",
            "report_phase": phase_id,
            "report_detail": "benchmark_reported",
        }

    return {
        "benchmark_report_status": "incomplete",
        "report_phase": None,
        "report_detail": None,
    }
