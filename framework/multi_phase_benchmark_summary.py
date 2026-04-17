from typing import Any


def summarize_benchmark(
    benchmark_control_plane: dict[str, Any],
    benchmark_scorer: dict[str, Any],
    promotion_readiness: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_control_plane, dict)
        or not isinstance(benchmark_scorer, dict)
        or not isinstance(promotion_readiness, dict)
    ):
        return {
            "benchmark_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_level": None,
        }

    bcp_ok = benchmark_control_plane.get("benchmark_cp_status") == "operational"
    bs_ok = benchmark_scorer.get("benchmark_score_status") == "scored"
    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"
    all_ok = bcp_ok and bs_ok and pr_ok

    if all_ok:
        return {
            "benchmark_summary_status": "complete",
            "summary_phase": benchmark_control_plane.get("cp_phase"),
            "summary_level": "detailed",
        }

    if (bcp_ok and bs_ok) or (bcp_ok and pr_ok) or (bs_ok and pr_ok):
        return {
            "benchmark_summary_status": "partial",
            "summary_phase": None,
            "summary_level": None,
        }

    return {
        "benchmark_summary_status": "incomplete",
        "summary_phase": None,
        "summary_level": None,
    }
