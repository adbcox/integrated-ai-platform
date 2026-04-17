from typing import Any


def consolidate_sign_offs(
    sign_off_aggregation: dict[str, Any],
    enforcement_result: dict[str, Any],
    registry_audit: dict[str, Any],
    handoff_rollup: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(sign_off_aggregation, dict)
        or not isinstance(enforcement_result, dict)
        or not isinstance(registry_audit, dict)
        or not isinstance(handoff_rollup, dict)
    ):
        return {
            "consolidation_valid": False,
            "aggregation_passed": False,
            "enforcement_approved": False,
            "registry_complete": False,
            "handoffs_approved": False,
            "consolidated_sign_off": False,
            "blocking_signals": [],
            "consolidation_status": "invalid_input",
        }

    aggregation_passed = sign_off_aggregation.get("aggregation_status") == "gate_passed"
    enforcement_approved = enforcement_result.get("enforcement_status") == "approved"
    registry_complete = registry_audit.get("registry_audit_status") == "complete"
    handoffs_approved = handoff_rollup.get("rollup_status") == "all_approved"

    blocking = []
    if not aggregation_passed:
        blocking.append("aggregation_passed")
    if not enforcement_approved:
        blocking.append("enforcement_approved")
    if not registry_complete:
        blocking.append("registry_complete")
    if not handoffs_approved:
        blocking.append("handoffs_approved")

    consolidated = len(blocking) == 0

    if consolidated:
        status = "signed_off"
    elif len(blocking) > 2:
        status = "blocked"
    else:
        status = "pending"

    return {
        "consolidation_valid": True,
        "aggregation_passed": aggregation_passed,
        "enforcement_approved": enforcement_approved,
        "registry_complete": registry_complete,
        "handoffs_approved": handoffs_approved,
        "consolidated_sign_off": consolidated,
        "blocking_signals": blocking,
        "consolidation_status": status,
    }


def summarize_sign_off_consolidation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("consolidation_valid") is not True:
        return {
            "summary_valid": False,
            "consolidation_status": "invalid_input",
            "consolidated_sign_off": False,
            "blocking_signal_count": 0,
        }

    return {
        "summary_valid": True,
        "consolidation_status": result.get("consolidation_status", "invalid_input"),
        "consolidated_sign_off": bool(result.get("consolidated_sign_off", False)),
        "blocking_signal_count": (
            len(result.get("blocking_signals", []))
            if isinstance(result.get("blocking_signals", []), list)
            else 0
        ),
    }
