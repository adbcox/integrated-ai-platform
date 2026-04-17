from typing import Any


def summarize_intelligence(
    learning_cp: dict[str, Any],
    audit: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(learning_cp, dict)
        or not isinstance(audit, dict)
        or not isinstance(recommendation, dict)
    ):
        return {
            "intelligence_summary_status": "invalid_input",
            "summary_phase": None,
            "intelligence_health": "degraded",
        }

    cp_op = learning_cp.get("learning_cp_status") == "operational"
    audit_ok = audit.get("learning_audit_status") in ("passed", "degraded")
    rec_ok = recommendation.get("recommendation_status") == "generated"

    if cp_op and audit_ok and rec_ok:
        return {
            "intelligence_summary_status": "complete",
            "summary_phase": learning_cp.get("learning_phase"),
            "intelligence_health": "healthy",
        }

    if cp_op and (not audit_ok or not rec_ok):
        return {
            "intelligence_summary_status": "partial",
            "summary_phase": None,
            "intelligence_health": "degraded",
        }

    return {
        "intelligence_summary_status": "failed",
        "summary_phase": None,
        "intelligence_health": "degraded",
    }
