from typing import Any


def emit_orchestration_telemetry(
    session_summary: dict[str, Any],
    dashboard_result: dict[str, Any],
    phase_report: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(session_summary, dict)
        or not isinstance(dashboard_result, dict)
        or not isinstance(phase_report, dict)
    ):
        return {
            "emit_valid": False,
            "records": [],
            "record_count": 0,
            "emit_status": "invalid_input",
        }

    records = [
        {
            "dimension": "session",
            "plan_id": session_summary.get("plan_id", "unknown"),
            "session_outcome": session_summary.get("session_outcome", "unknown"),
            "completed_count": int(session_summary.get("completed_count", 0)),
            "elapsed_seconds": float(session_summary.get("elapsed_seconds", 0.0)),
        },
        {
            "dimension": "dashboard",
            "overall_operational_status": dashboard_result.get(
                "overall_operational_status", "unknown"
            ),
            "health_score": float(dashboard_result.get("health_score", 0.0)),
            "alert_count": int(dashboard_result.get("alert_count", 0)),
        },
        {
            "dimension": "phase",
            "phase_report_status": phase_report.get("phase_report_status", "unknown"),
            "phase_completion_pct": float(phase_report.get("phase_completion_pct", 0.0)),
            "workflow_count": int(phase_report.get("workflow_count", 0)),
        },
    ]

    return {
        "emit_valid": True,
        "records": records,
        "record_count": len(records),
        "emit_status": "emitted" if len(records) == 3 else "partial",
    }


def summarize_telemetry(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("emit_valid") is not True:
        return {
            "summary_valid": False,
            "emit_status": "invalid_input",
            "record_count": 0,
        }

    return {
        "summary_valid": True,
        "emit_status": result.get("emit_status", "invalid_input"),
        "record_count": int(result.get("record_count", 0)),
    }
