from typing import Any


def run_benchmarks(
    benchmark_schedule: dict[str, Any],
    simulation_results: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_schedule, dict)
        or not isinstance(simulation_results, dict)
        or not isinstance(config, dict)
    ):
        return {
            "run_status": "invalid_input",
            "run_count": 0,
            "run_phase": None,
        }

    bs_ok = benchmark_schedule.get("benchmark_schedule_status") == "scheduled"
    sr_ok = simulation_results.get("simulation_status") == "simulated"
    all_ok = bs_ok and sr_ok

    if all_ok:
        return {
            "run_status": "run",
            "run_count": benchmark_schedule.get("benchmark_count", 0),
            "run_phase": benchmark_schedule.get("benchmark_phase"),
        }

    return {
        "run_status": "failed",
        "run_count": 0,
        "run_phase": None,
    }
