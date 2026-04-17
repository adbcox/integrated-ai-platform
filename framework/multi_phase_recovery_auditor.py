from typing import Any


def audit_recovery(
    retry_result: dict[str, Any],
    failover_result: dict[str, Any],
    reconciliation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(retry_result, dict)
        or not isinstance(failover_result, dict)
        or not isinstance(reconciliation, dict)
    ):
        return {
            "audit_status": "invalid_input",
            "recovery_path": "none",
            "reconciliation_status": None,
        }

    any_action = (
        retry_result.get("retry_status") in ("retried", "exhausted")
        or failover_result.get("failover_status") in ("routed", "no_fallback")
    )
    recovery_succeeded = (
        retry_result.get("retry_status") == "retried"
        or failover_result.get("failover_status") == "routed"
    )

    if not any_action:
        return {
            "audit_status": "no_recovery_attempted",
            "recovery_path": "none",
            "reconciliation_status": reconciliation.get("reconciliation_status"),
        }

    if recovery_succeeded:
        return {
            "audit_status": "passed",
            "recovery_path": (
                "retry"
                if retry_result.get("retry_status") == "retried"
                else "failover"
            ),
            "reconciliation_status": reconciliation.get("reconciliation_status"),
        }

    return {
        "audit_status": "failed",
        "recovery_path": "none",
        "reconciliation_status": reconciliation.get("reconciliation_status"),
    }
