from typing import Any


def rollup_optimization(
    optimization: dict[str, Any],
    tuning: dict[str, Any],
    reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(optimization, dict)
        or not isinstance(tuning, dict)
        or not isinstance(reporter, dict)
    ):
        return {
            "optimization_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        optimization.get("optimization_status") == "optimized"
        and tuning.get("tuning_status") == "tuned"
        and reporter.get("adaptation_report_status") == "complete"
    )

    count = sum(
        1
        for s, vals in [
            (optimization.get("optimization_status"), ("optimized",)),
            (tuning.get("tuning_status"), ("tuned",)),
            (reporter.get("adaptation_report_status"), ("complete",)),
        ]
        if s in vals
    )

    if all_complete:
        return {
            "optimization_rollup_status": "rolled_up",
            "rollup_phase": reporter.get("report_phase"),
            "operations_complete": count,
        }

    return {
        "optimization_rollup_status": "incomplete_source",
        "rollup_phase": None,
        "operations_complete": count,
    }
