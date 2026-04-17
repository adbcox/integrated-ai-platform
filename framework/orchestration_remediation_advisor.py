from typing import Any


def advise_remediation(
    alert_result: dict[str, Any],
    blocking_result: dict[str, Any],
    retry_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(alert_result, dict)
        or not isinstance(blocking_result, dict)
        or not isinstance(retry_result, dict)
    ):
        return {
            "advisor_valid": False,
            "recommendations": [],
            "recommendation_count": 0,
            "has_immediate_actions": False,
            "advisor_status": "invalid_input",
        }

    recommendations = []

    if blocking_result.get("blocking_type") == "deadlock":
        recommendations.append(
            {
                "priority": "immediate",
                "action": "kill_and_retry",
                "target": "blocking_jobs",
            }
        )

    if blocking_result.get("blocking_type") == "stall":
        recommendations.append(
            {
                "priority": "immediate",
                "action": "force_advance",
                "target": "active_stage",
            }
        )

    if retry_result.get("schedule_status") == "all_unretryable":
        recommendations.append(
            {
                "priority": "high",
                "action": "manual_intervention",
                "target": "failed_jobs",
            }
        )

    if int(alert_result.get("critical_count", 0)) > 0:
        recommendations.append(
            {
                "priority": "high",
                "action": "escalate_to_operator",
                "target": "orchestration_stack",
            }
        )

    if int(alert_result.get("warning_count", 0)) > 0:
        recommendations.append(
            {
                "priority": "normal",
                "action": "monitor_and_retry",
                "target": "retry_candidates",
            }
        )

    deduped = []
    seen = set()
    for rec in recommendations:
        key = (
            rec.get("priority", ""),
            rec.get("action", ""),
            rec.get("target", ""),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(rec)

    return {
        "advisor_valid": True,
        "recommendations": deduped,
        "recommendation_count": len(deduped),
        "has_immediate_actions": any(
            rec.get("priority") == "immediate" for rec in deduped
        ),
        "advisor_status": "no_action" if len(deduped) == 0 else "advised",
    }


def summarize_remediation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("advisor_valid") is not True:
        return {
            "summary_valid": False,
            "advisor_status": "invalid_input",
            "recommendation_count": 0,
            "has_immediate_actions": False,
        }

    return {
        "summary_valid": True,
        "advisor_status": result.get("advisor_status", "invalid_input"),
        "recommendation_count": int(result.get("recommendation_count", 0)),
        "has_immediate_actions": bool(result.get("has_immediate_actions", False)),
    }
