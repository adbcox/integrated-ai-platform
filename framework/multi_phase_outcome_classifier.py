from typing import Any


def classify_outcome(
    outcome: dict[str, Any], sla: dict[str, Any], health: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(outcome, dict)
        or not isinstance(sla, dict)
        or not isinstance(health, dict)
    ):
        return {"classification_status": "invalid_input", "classified_phase": None, "decision_id": None}

    outcome_ok = outcome.get("outcome_status") == "collected"
    sla_met = sla.get("sla_status") == "met"
    sla_at_risk = sla.get("sla_status") == "at_risk"
    sla_breach = sla.get("sla_status") == "breached"
    health_healthy = health.get("health_status") == "healthy"
    health_critical = health.get("health_status") == "critical"

    if outcome_ok and sla_met and health_healthy:
        return {
            "classification_status": "success",
            "classified_phase": outcome.get("outcome_phase"),
            "decision_id": outcome.get("decision_id"),
        }

    if outcome_ok and sla_at_risk and not health_critical:
        return {
            "classification_status": "partial_success",
            "classified_phase": outcome.get("outcome_phase"),
            "decision_id": outcome.get("decision_id"),
        }

    if outcome_ok and (sla_breach or health_critical):
        return {
            "classification_status": "failure",
            "classified_phase": outcome.get("outcome_phase"),
            "decision_id": outcome.get("decision_id"),
        }

    if not outcome_ok:
        return {"classification_status": "no_outcome", "classified_phase": None, "decision_id": None}

    return {"classification_status": "invalid_input", "classified_phase": None, "decision_id": None}
