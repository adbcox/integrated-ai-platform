from typing import Any


def rollup_policy(
    enforcement: dict[str, Any],
    compliance: dict[str, Any],
    reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(enforcement, dict)
        or not isinstance(compliance, dict)
        or not isinstance(reporter, dict)
    ):
        return {
            "policy_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        enforcement.get("enforcement_status") == "enforced"
        and compliance.get("compliance_status") in ("compliant", "partial")
        and reporter.get("governance_report_status") == "complete"
    )

    count = sum(
        1
        for s, vals in [
            (enforcement.get("enforcement_status"), ("enforced",)),
            (compliance.get("compliance_status"), ("compliant", "partial")),
            (reporter.get("governance_report_status"), ("complete",)),
        ]
        if s in vals
    )

    if all_complete:
        return {
            "policy_rollup_status": "rolled_up",
            "rollup_phase": reporter.get("report_phase"),
            "operations_complete": count,
        }

    return {
        "policy_rollup_status": "incomplete_source",
        "rollup_phase": None,
        "operations_complete": count,
    }
