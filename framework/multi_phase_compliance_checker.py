from typing import Any


def check_compliance(
    enforcement: dict[str, Any],
    sla: dict[str, Any],
    budget_gov: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(enforcement, dict)
        or not isinstance(sla, dict)
        or not isinstance(budget_gov, dict)
    ):
        return {
            "compliance_status": "invalid_input",
            "ok_count": 0,
            "compliance_phase": None,
        }

    enforce_ok = enforcement.get("enforcement_status") == "enforced"
    sla_ok = sla.get("sla_status") in ("met", "at_risk")
    budget_ok = budget_gov.get("governance_status") in ("within_budget", "over_budget")

    all_ok = enforce_ok and sla_ok and budget_ok
    any_ok = enforce_ok or sla_ok or budget_ok
    ok_count = sum([enforce_ok, sla_ok, budget_ok])

    if all_ok:
        return {
            "compliance_status": "compliant",
            "ok_count": ok_count,
            "compliance_phase": enforcement.get("enforced_phase"),
        }

    if any_ok:
        return {
            "compliance_status": "partial",
            "ok_count": ok_count,
            "compliance_phase": None,
        }

    return {
        "compliance_status": "non_compliant",
        "ok_count": ok_count,
        "compliance_phase": None,
    }
