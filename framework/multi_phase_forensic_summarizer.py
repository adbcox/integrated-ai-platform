from typing import Any


def summarize_forensics(
    incident: dict[str, Any],
    diagnostic: dict[str, Any],
    trace: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(incident, dict)
        or not isinstance(diagnostic, dict)
        or not isinstance(trace, dict)
    ):
        return {
            "forensic_status": "invalid_input",
            "forensic_phase": None,
            "evidence_count": 0,
        }

    incident_active = incident.get("incident_status") in ("critical", "warning")
    diagnostic_routed = diagnostic.get("diagnostic_status") == "routed"
    trace_ok = trace.get("trace_status") == "recorded"

    evidence_count = sum([incident_active, diagnostic_routed, trace_ok])

    if incident_active and diagnostic_routed and trace_ok:
        return {
            "forensic_status": "complete",
            "forensic_phase": incident.get("incident_phase"),
            "evidence_count": evidence_count,
        }

    if (
        trace_ok
        and (incident_active or diagnostic_routed)
        and not (incident_active and diagnostic_routed)
    ):
        return {
            "forensic_status": "partial",
            "forensic_phase": None,
            "evidence_count": evidence_count,
        }

    if not incident_active:
        return {
            "forensic_status": "nominal",
            "forensic_phase": None,
            "evidence_count": evidence_count,
        }

    return {
        "forensic_status": "invalid_input",
        "forensic_phase": None,
        "evidence_count": evidence_count,
    }
