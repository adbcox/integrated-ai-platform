from typing import Any


def route_escalation(
    blocking_result: dict[str, Any],
    completion_result: dict[str, Any],
    escalation_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(blocking_result, dict)
        or not isinstance(completion_result, dict)
        or not isinstance(escalation_policy, dict)
    ):
        return {
            "routing_valid": False,
            "should_escalate": False,
            "escalation_target": "default",
            "escalation_reason": "none",
            "routing_status": "invalid_input",
        }

    should_escalate = False
    escalation_reason = "none"

    if (
        escalation_policy.get("escalate_on_deadlock")
        and blocking_result.get("blocking_type") == "deadlock"
    ):
        should_escalate = True
        escalation_reason = "deadlock"
    elif (
        escalation_policy.get("escalate_on_stall")
        and blocking_result.get("blocking_type") == "stall"
    ):
        should_escalate = True
        escalation_reason = "stall"
    elif (
        escalation_policy.get("escalate_on_partial_failure")
        and completion_result.get("completion_type") in ("partial_failure",)
    ):
        should_escalate = True
        escalation_reason = "partial_failure"

    escalation_target = escalation_policy.get("escalation_target", "default")
    routing_status = "escalated" if should_escalate else "not_escalated"

    return {
        "routing_valid": True,
        "should_escalate": should_escalate,
        "escalation_target": escalation_target,
        "escalation_reason": escalation_reason,
        "routing_status": routing_status,
    }


def summarize_escalation_routing(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("routing_valid") is not True:
        return {
            "summary_valid": False,
            "should_escalate": False,
            "escalation_reason": "none",
            "routing_status": "invalid_input",
        }

    return {
        "summary_valid": True,
        "should_escalate": bool(result.get("should_escalate", False)),
        "escalation_reason": result.get("escalation_reason", "none"),
        "routing_status": result.get("routing_status", "invalid_input"),
    }
