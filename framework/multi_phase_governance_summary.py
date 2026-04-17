from typing import Any


def summarize_governance(
    governance_cp: dict[str, Any],
    sla: dict[str, Any],
    compliance: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(governance_cp, dict)
        or not isinstance(sla, dict)
        or not isinstance(compliance, dict)
    ):
        return {
            "governance_summary_status": "invalid_input",
            "summary_phase": None,
            "governance_health": "degraded",
        }

    cp_operational = governance_cp.get("governance_cp_status") == "operational"
    sla_ok = sla.get("sla_status") in ("met", "at_risk")
    compliance_ok = compliance.get("compliance_status") in ("compliant", "partial")

    if cp_operational and sla_ok and compliance_ok:
        return {
            "governance_summary_status": "complete",
            "summary_phase": governance_cp.get("governance_phase"),
            "governance_health": "healthy",
        }

    if cp_operational and (not sla_ok or not compliance_ok):
        return {
            "governance_summary_status": "partial",
            "summary_phase": None,
            "governance_health": "degraded",
        }

    return {
        "governance_summary_status": "failed",
        "summary_phase": None,
        "governance_health": "degraded",
    }
