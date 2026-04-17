from typing import Any


def rollup_handoffs(handoff_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(handoff_results, list):
        return {
            "rollup_valid": False,
            "handoff_count": 0,
            "approved_count": 0,
            "pending_count": 0,
            "blocked_count": 0,
            "total_workflows": 0,
            "approval_rate": 0.0,
            "all_approved": False,
            "rollup_status": "invalid_input",
        }

    valid = [
        h for h in handoff_results if isinstance(h, dict) and h.get("handoff_valid") is True
    ]
    if len(valid) == 0:
        return {
            "rollup_valid": True,
            "handoff_count": 0,
            "approved_count": 0,
            "pending_count": 0,
            "blocked_count": 0,
            "total_workflows": 0,
            "approval_rate": 0.0,
            "all_approved": False,
            "rollup_status": "empty",
        }

    handoff_count = len(valid)
    approved_count = len([h for h in valid if h.get("handoff_approved") is True])
    pending_count = len([h for h in valid if h.get("handoff_status") == "pending"])
    blocked_count = len([h for h in valid if h.get("handoff_status") == "blocked"])
    total_workflows = sum(int(h.get("workflow_count", 0)) for h in valid)
    approval_rate = (
        round((approved_count / float(handoff_count)) * 100.0, 3)
        if handoff_count > 0
        else 0.0
    )
    all_approved = handoff_count > 0 and approved_count == handoff_count

    if all_approved:
        status = "all_approved"
    elif approved_count == 0 and handoff_count > 0:
        status = "none_approved"
    else:
        status = "partial"

    return {
        "rollup_valid": True,
        "handoff_count": handoff_count,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "blocked_count": blocked_count,
        "total_workflows": total_workflows,
        "approval_rate": approval_rate,
        "all_approved": all_approved,
        "rollup_status": status,
    }


def summarize_handoff_rollup(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("rollup_valid") is not True:
        return {
            "summary_valid": False,
            "rollup_status": "invalid_input",
            "approval_rate": 0.0,
            "total_workflows": 0,
        }

    return {
        "summary_valid": True,
        "rollup_status": result.get("rollup_status", "invalid_input"),
        "approval_rate": float(result.get("approval_rate", 0.0)),
        "total_workflows": int(result.get("total_workflows", 0)),
    }
