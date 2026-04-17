from typing import Any


def audit_policy(
    enforcement: dict[str, Any],
    compliance: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(enforcement, dict)
        or not isinstance(compliance, dict)
        or not isinstance(approval, dict)
    ):
        return {
            "policy_audit_status": "invalid_input",
            "ok_count": 0,
            "audit_phase": None,
        }

    enforce_ok = enforcement.get("enforcement_status") == "enforced"
    compliance_ok = compliance.get("compliance_status") in ("compliant", "partial")
    approval_ok = approval.get("approval_status") in ("approved", "pending")

    all_ok = enforce_ok and compliance_ok and approval_ok
    any_ok = enforce_ok or compliance_ok or approval_ok
    ok_count = sum([enforce_ok, compliance_ok, approval_ok])

    if all_ok:
        return {
            "policy_audit_status": "passed",
            "ok_count": ok_count,
            "audit_phase": enforcement.get("enforced_phase"),
        }

    if any_ok:
        return {
            "policy_audit_status": "degraded",
            "ok_count": ok_count,
            "audit_phase": None,
        }

    return {
        "policy_audit_status": "failed",
        "ok_count": ok_count,
        "audit_phase": None,
    }
