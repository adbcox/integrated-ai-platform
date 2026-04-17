from typing import Any


def score_benchmarks(
    benchmark_runner: dict[str, Any],
    mastery_assessment: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_runner, dict)
        or not isinstance(mastery_assessment, dict)
        or not isinstance(config, dict)
    ):
        return {
            "benchmark_score_status": "invalid_input",
            "benchmark_score": None,
            "score_phase": None,
        }

    br_ok = benchmark_runner.get("run_status") == "run"
    ma_ok = mastery_assessment.get("mastery_status") == "assessed"
    all_ok = br_ok and ma_ok

    if all_ok:
        return {
            "benchmark_score_status": "scored",
            "benchmark_score": mastery_assessment.get("mastery_score"),
            "score_phase": benchmark_runner.get("run_phase"),
        }

    return {
        "benchmark_score_status": "failed",
        "benchmark_score": None,
        "score_phase": None,
    }
