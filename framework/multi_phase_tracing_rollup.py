from typing import Any


def rollup_tracing(
    trace: dict[str, Any],
    correlation: dict[str, Any],
    forensic: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(trace, dict)
        or not isinstance(correlation, dict)
        or not isinstance(forensic, dict)
    ):
        return {
            "tracing_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        trace.get("trace_status") == "recorded"
        and correlation.get("correlation_status")
        in ("correlated", "no_alerts")
        and forensic.get("forensic_status")
        in ("complete", "partial", "nominal")
    )

    count = sum(
        1
        for s, vals in [
            (trace.get("trace_status"), ("recorded",)),
            (correlation.get("correlation_status"), ("correlated", "no_alerts")),
            (forensic.get("forensic_status"), ("complete", "partial", "nominal")),
        ]
        if s in vals
    )

    if all_complete:
        return {
            "tracing_rollup_status": "rolled_up",
            "rollup_phase": trace.get("trace_phase"),
            "operations_complete": count,
        }

    return {
        "tracing_rollup_status": "incomplete_source",
        "rollup_phase": None,
        "operations_complete": count,
    }
