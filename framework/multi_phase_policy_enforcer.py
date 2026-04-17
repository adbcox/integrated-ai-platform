from typing import Any


def enforce_policy(
    admission: dict[str, Any],
    resilience_summary: dict[str, Any],
    policy_rules: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(admission, dict)
        or not isinstance(resilience_summary, dict)
        or not isinstance(policy_rules, dict)
    ):
        return {
            "enforcement_status": "invalid_input",
            "enforced_phase": None,
            "rules_applied": 0,
        }

    if admission.get("admission_status") != "admitted":
        return {
            "enforcement_status": "no_admission",
            "enforced_phase": None,
            "rules_applied": 0,
        }

    if resilience_summary.get("summary_status") == "failed":
        return {
            "enforcement_status": "blocked",
            "enforced_phase": None,
            "rules_applied": 0,
        }

    if resilience_summary.get("summary_status") in ("complete", "partial"):
        return {
            "enforcement_status": "enforced",
            "enforced_phase": admission.get("admitted_phase"),
            "rules_applied": len(policy_rules),
        }

    return {
        "enforcement_status": "invalid_input",
        "enforced_phase": None,
        "rules_applied": 0,
    }
