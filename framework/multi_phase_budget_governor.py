from typing import Any


def govern_budget(
    quota: dict[str, Any],
    retry_budget: dict[str, Any],
    budget_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(quota, dict)
        or not isinstance(retry_budget, dict)
        or not isinstance(budget_policy, dict)
    ):
        return {
            "governance_status": "invalid_input",
            "budget_phase": None,
            "remaining": 0,
        }

    quota_active = quota.get("quota_status") == "active"
    budget_active = retry_budget.get("budget_status") == "active"
    quota_exists = quota.get("quota_status") in ("active", "exceeded")
    budget_exists = retry_budget.get("budget_status") in ("active", "exhausted")

    if quota_active and budget_active:
        return {
            "governance_status": "within_budget",
            "budget_phase": quota.get("quota_phase"),
            "remaining": int(retry_budget.get("remaining_budget", 0)),
        }

    if quota_exists and budget_exists and not (quota_active and budget_active):
        return {
            "governance_status": "over_budget",
            "budget_phase": None,
            "remaining": 0,
        }

    if not quota_exists:
        return {
            "governance_status": "no_quota",
            "budget_phase": None,
            "remaining": 0,
        }

    return {
        "governance_status": "invalid_input",
        "budget_phase": None,
        "remaining": 0,
    }
