from typing import Any


def summarize_autonomy(
    autonomy_cp: dict[str, Any],
    audit: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(autonomy_cp, dict)
        or not isinstance(audit, dict)
        or not isinstance(report, dict)
    ):
        return {
            "autonomy_summary_status": "invalid_input",
            "summary_phase": None,
            "autonomy_health": "degraded",
        }

    cp_op = autonomy_cp.get("autonomy_cp_status") == "operational"
    audit_ok = audit.get("autonomy_audit_status") in ("passed", "degraded")
    report_ok = report.get("autonomy_report_status") == "complete"

    if cp_op and audit_ok and report_ok:
        return {
            "autonomy_summary_status": "complete",
            "summary_phase": autonomy_cp.get("autonomy_phase"),
            "autonomy_health": "healthy",
        }

    if cp_op and (not audit_ok or not report_ok):
        return {
            "autonomy_summary_status": "partial",
            "summary_phase": None,
            "autonomy_health": "degraded",
        }

    return {
        "autonomy_summary_status": "failed",
        "summary_phase": None,
        "autonomy_health": "degraded",
    }
