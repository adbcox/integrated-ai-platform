from typing import Any


def rollup_metrics(
    metrics: dict[str, Any],
    trace: dict[str, Any],
    reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(metrics, dict)
        or not isinstance(trace, dict)
        or not isinstance(reporter, dict)
    ):
        return {
            "metrics_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        metrics.get("metrics_status") == "collected"
        and trace.get("trace_status") == "recorded"
        and reporter.get("observability_report_status") == "complete"
    )

    count = sum(
        1
        for s, vals in [
            (metrics.get("metrics_status"), ("collected",)),
            (trace.get("trace_status"), ("recorded",)),
            (reporter.get("observability_report_status"), ("complete",)),
        ]
        if s in vals
    )

    if all_complete:
        return {
            "metrics_rollup_status": "rolled_up",
            "rollup_phase": reporter.get("report_phase"),
            "operations_complete": count,
        }

    return {
        "metrics_rollup_status": "incomplete_source",
        "rollup_phase": None,
        "operations_complete": count,
    }
