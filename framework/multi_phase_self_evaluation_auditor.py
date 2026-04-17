from typing import Any


def audit_self_evaluation(
    critique_auditor: dict[str, Any],
    adversarial_tester: dict[str, Any],
    policy_stress_tester: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(critique_auditor, dict)
        or not isinstance(adversarial_tester, dict)
        or not isinstance(policy_stress_tester, dict)
    ):
        return {
            "self_eval_audit_status": "invalid_input",
            "audit_phase": None,
            "audit_result": None,
        }

    ca_ok = critique_auditor.get("critique_audit_status") == "passed"
    at_ok = adversarial_tester.get("adversarial_status") == "tested"
    pst_ok = policy_stress_tester.get("stress_status") == "stressed"
    all_ok = ca_ok and at_ok and pst_ok

    if all_ok:
        return {
            "self_eval_audit_status": "passed",
            "audit_phase": critique_auditor.get("audit_phase"),
            "audit_result": "self_eval_valid",
        }

    if (ca_ok and at_ok) or (ca_ok and pst_ok):
        return {
            "self_eval_audit_status": "degraded",
            "audit_phase": None,
            "audit_result": None,
        }

    return {
        "self_eval_audit_status": "failed",
        "audit_phase": None,
        "audit_result": None,
    }
