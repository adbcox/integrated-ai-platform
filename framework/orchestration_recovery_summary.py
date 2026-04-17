from typing import Any


def build_recovery_summary(
    reconcile_result: dict[str, Any],
    validation_result: dict[str, Any],
    resumption_result: dict[str, Any],
    retry_schedule_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(reconcile_result, dict)
        or not isinstance(validation_result, dict)
        or not isinstance(resumption_result, dict)
        or not isinstance(retry_schedule_result, dict)
    ):
        return {
            "summary_valid": False,
            "reconcile_status": "unknown",
            "checkpoint_valid": False,
            "resumption_action": "unknown",
            "retry_count": 0,
            "jobs_pending": 0,
            "recovery_viable": False,
            "recovery_status": "invalid_input",
        }

    recovery_viable = (
        reconcile_result.get("reconcile_valid", False)
        and validation_result.get("validation_valid", False)
        and resumption_result.get("coordination_valid", False)
    )

    retry_entries = retry_schedule_result.get("retry_entries", [])
    jobs_pending = resumption_result.get("jobs_pending", [])

    if not isinstance(retry_entries, list):
        retry_entries = []
    if not isinstance(jobs_pending, list):
        jobs_pending = []

    return {
        "summary_valid": True,
        "reconcile_status": reconcile_result.get("reconcile_status", "unknown"),
        "checkpoint_valid": validation_result.get("validation_status") == "valid",
        "resumption_action": resumption_result.get(
            "resumption_action", "unknown"
        ),
        "retry_count": len(retry_entries),
        "jobs_pending": len(jobs_pending),
        "recovery_viable": recovery_viable,
        "recovery_status": "viable" if recovery_viable else "non_viable",
    }


def summarize_recovery(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("summary_valid") is not True:
        return {
            "summary_valid": False,
            "recovery_status": "invalid_input",
            "recovery_viable": False,
        }

    return {
        "summary_valid": True,
        "recovery_status": result.get("recovery_status", "invalid_input"),
        "recovery_viable": bool(result.get("recovery_viable", False)),
    }
