from typing import Any


def tune_from_diagnostics(
    optimization: dict[str, Any],
    observability_cp: dict[str, Any],
    diagnostic_hints: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(optimization, dict)
        or not isinstance(observability_cp, dict)
        or not isinstance(diagnostic_hints, dict)
    ):
        return {
            "diagnostic_tuning_status": "invalid_input",
            "tuned_phase": None,
            "hints_count": 0,
        }

    opt_ok = optimization.get("optimization_status") == "optimized"
    obs_op = observability_cp.get("observability_cp_status") == "operational"

    if not opt_ok:
        return {
            "diagnostic_tuning_status": "no_optimization",
            "tuned_phase": None,
            "hints_count": 0,
        }

    if opt_ok and not obs_op:
        return {
            "diagnostic_tuning_status": "observability_offline",
            "tuned_phase": None,
            "hints_count": 0,
        }

    return {
        "diagnostic_tuning_status": "tuned",
        "tuned_phase": observability_cp.get("observability_phase"),
        "hints_count": len(diagnostic_hints),
    }
