from typing import Any


def rollup_benchmark(
    benchmark_runner: dict[str, Any],
    benchmark_scorer: dict[str, Any],
    benchmark_reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_runner, dict)
        or not isinstance(benchmark_scorer, dict)
        or not isinstance(benchmark_reporter, dict)
    ):
        return {
            "benchmark_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    br_ok = benchmark_runner.get("run_status") == "run"
    bs_ok = benchmark_scorer.get("benchmark_score_status") == "scored"
    brepo_ok = benchmark_reporter.get("benchmark_report_status") == "complete"
    all_ok = br_ok and bs_ok and brepo_ok

    if all_ok:
        return {
            "benchmark_rollup_status": "rolled_up",
            "rollup_phase": benchmark_runner.get("run_phase"),
            "rollup_count": benchmark_runner.get("run_count", 0),
        }

    if (br_ok and bs_ok) or (br_ok and brepo_ok):
        return {
            "benchmark_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "benchmark_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
