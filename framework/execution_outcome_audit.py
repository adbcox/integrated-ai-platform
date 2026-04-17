from typing import Any

def audit_outcome_eligibility(outcome_class: str, attempts_used: int, retry_budget: int) -> dict[str, Any]:
    is_retry_eligible = outcome_class == "retry_eligible" and attempts_used < retry_budget
    return {
        "outcome_class": outcome_class,
        "attempts_used": attempts_used,
        "retry_budget": retry_budget,
        "is_retry_eligible": is_retry_eligible,
        "retries_remaining": max(0, retry_budget - attempts_used) if outcome_class == "retry_eligible" else 0
    }

def generate_outcome_audit_trail(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    if not outcomes:
        return {"total_outcomes_audited": 0, "success_count": 0, "retry_eligible_count": 0, "terminal_failure_count": 0, "unknown_count": 0, "success_rate_percent": 0}
    success_count = sum(1 for o in outcomes if isinstance(o, dict) and o.get("outcome_class") == "success")
    failure_count = sum(1 for o in outcomes if isinstance(o, dict) and o.get("outcome_class") in ["terminal_failure", "escalated"])
    retry_count = sum(1 for o in outcomes if isinstance(o, dict) and o.get("outcome_class") == "retry_eligible")
    unknown_count = len(outcomes) - success_count - failure_count - retry_count
    return {
        "total_outcomes_audited": len(outcomes),
        "success_count": success_count,
        "retry_eligible_count": retry_count,
        "terminal_failure_count": failure_count,
        "unknown_count": unknown_count,
        "success_rate_percent": round(success_count / float(len(outcomes)) * 100, 1) if outcomes else 0
    }

def check_escalation_patterns(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    if not outcomes:
        return {"total_outcomes": 0, "escalation_count": 0, "escalation_rate_percent": 0, "needs_review": False}
    escalated = sum(1 for o in outcomes if isinstance(o, dict) and o.get("outcome_class") == "escalated")
    escalation_rate = round(escalated / float(len(outcomes)) * 100, 1) if outcomes else 0
    return {
        "total_outcomes": len(outcomes),
        "escalation_count": escalated,
        "escalation_rate_percent": escalation_rate,
        "needs_review": escalation_rate > 20
    }

def compute_retry_burden(outcomes: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    retry_eligible = sum(1 for o in outcomes if isinstance(o, dict) and o.get("outcome_class") == "retry_eligible")
    retry_events = sum(1 for e in events if isinstance(e, dict) and "retry" in e.get("event_type", "").lower())
    total_retries = retry_eligible + retry_events
    return {
        "retry_eligible_outcomes": retry_eligible,
        "retry_events_recorded": retry_events,
        "total_potential_retries": total_retries,
        "high_retry_burden": total_retries > 10
    }
