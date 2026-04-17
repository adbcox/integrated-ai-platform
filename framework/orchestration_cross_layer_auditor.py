from typing import Any


def audit_cross_layer(
    integration_result: dict[str, Any],
    health_result: dict[str, Any],
    end_state_result: dict[str, Any],
    rollup_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(integration_result, dict)
        or not isinstance(health_result, dict)
        or not isinstance(end_state_result, dict)
        or not isinstance(rollup_result, dict)
    ):
        return {
            "audit_valid": False,
            "integration_passed": False,
            "health_passed": False,
            "end_state_passed": False,
            "rollup_passed": False,
            "all_passed": False,
            "failed_audits": [],
            "audit_status": "invalid_input",
        }

    integration_passed = integration_result.get("integration_status") == "integrated"
    health_passed = health_result.get("health_status") == "healthy"
    end_state_passed = end_state_result.get("end_state_status") == "valid"
    rollup_passed = rollup_result.get("rollup_status") == "consistent"

    failed_audits = []
    if not integration_passed:
        failed_audits.append("integration_passed")
    if not health_passed:
        failed_audits.append("health_passed")
    if not end_state_passed:
        failed_audits.append("end_state_passed")
    if not rollup_passed:
        failed_audits.append("rollup_passed")

    all_passed = len(failed_audits) == 0

    if all_passed:
        status = "passed"
    elif len(failed_audits) == 4:
        status = "failed"
    else:
        status = "partial_pass"

    return {
        "audit_valid": True,
        "integration_passed": integration_passed,
        "health_passed": health_passed,
        "end_state_passed": end_state_passed,
        "rollup_passed": rollup_passed,
        "all_passed": all_passed,
        "failed_audits": failed_audits,
        "audit_status": status,
    }


def summarize_cross_layer_audit(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("audit_valid") is not True:
        return {
            "summary_valid": False,
            "audit_status": "invalid_input",
            "failed_audit_count": 0,
        }

    return {
        "summary_valid": True,
        "audit_status": result.get("audit_status", "invalid_input"),
        "failed_audit_count": (
            len(result.get("failed_audits", []))
            if isinstance(result.get("failed_audits", []), list)
            else 0
        ),
    }
