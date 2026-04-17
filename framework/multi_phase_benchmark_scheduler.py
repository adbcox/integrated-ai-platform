from typing import Any


def schedule_benchmarks(
    scenarios: dict[str, Any],
    coordinator: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(scenarios, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(config, dict)
    ):
        return {
            "benchmark_schedule_status": "invalid_input",
            "benchmark_count": 0,
            "benchmark_phase": None,
        }

    s_ok = scenarios.get("scenario_status") == "generated"
    c_ok = coordinator.get("coordinator_status") == "initialized"
    all_ok = s_ok and c_ok

    if all_ok:
        return {
            "benchmark_schedule_status": "scheduled",
            "benchmark_count": config.get("count", 4),
            "benchmark_phase": scenarios.get("scenario_phase"),
        }

    return {
        "benchmark_schedule_status": "failed",
        "benchmark_count": 0,
        "benchmark_phase": None,
    }
