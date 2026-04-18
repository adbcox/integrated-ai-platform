from typing import Any

def route_incident_triage(incident_severity_scorer: Any, routing_config: Any) -> dict[str, Any]:
    if not isinstance(incident_severity_scorer, dict):
        return {"incident_triage_routing_status": "not_routed"}
    score_ok = incident_severity_scorer.get("incident_severity_scoring_status") == "scored"
    if not score_ok:
        return {"incident_triage_routing_status": "not_routed"}
    severity = incident_severity_scorer.get("severity_level", "P3")
    return {
        "incident_triage_routing_status": "routed",
        "escalation_target": "primary_oncall" if severity.startswith("P1") else "secondary_oncall",
    }
