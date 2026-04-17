from typing import Any


def rollup_simulation(
    scenario_simulator: dict[str, Any],
    robustness_scorer: dict[str, Any],
    self_evaluation_reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(scenario_simulator, dict)
        or not isinstance(robustness_scorer, dict)
        or not isinstance(self_evaluation_reporter, dict)
    ):
        return {
            "simulation_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    ss_ok = scenario_simulator.get("simulation_status") == "simulated"
    rs_ok = robustness_scorer.get("robustness_status") == "scored"
    ser_ok = self_evaluation_reporter.get("self_eval_report_status") == "complete"
    all_ok = ss_ok and rs_ok and ser_ok

    if all_ok:
        return {
            "simulation_rollup_status": "rolled_up",
            "rollup_phase": scenario_simulator.get("simulation_phase"),
            "rollup_count": scenario_simulator.get("simulation_count", 0),
        }

    if (ss_ok and rs_ok) or (ss_ok and ser_ok):
        return {
            "simulation_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "simulation_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
