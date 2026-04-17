from typing import Any


def schedule_job_retries(
    failed_job_ids: list[str],
    retry_history: dict[str, Any],
    retry_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(failed_job_ids, list)
        or not isinstance(retry_history, dict)
        or not isinstance(retry_policy, dict)
    ):
        return {
            "schedule_valid": False,
            "retry_entries": [],
            "unretryable_job_ids": [],
            "schedule_status": "invalid_input",
        }

    if not failed_job_ids:
        return {
            "schedule_valid": True,
            "retry_entries": [],
            "unretryable_job_ids": [],
            "schedule_status": "empty",
        }

    max_attempts = int(retry_policy.get("max_attempts", 0))
    base_delay_seconds = float(retry_policy.get("base_delay_seconds", 0.0))
    backoff_multiplier = float(retry_policy.get("backoff_multiplier", 1.0))

    retry_entries = []
    unretryable = []

    for job_id in failed_job_ids:
        attempt = int(retry_history.get(job_id, 0)) + 1
        delay = round(
            base_delay_seconds * (backoff_multiplier ** (attempt - 1)), 3
        )
        schedulable = attempt <= max_attempts

        entry = {
            "job_id": job_id,
            "attempt": attempt,
            "delay_seconds": delay,
            "schedulable": schedulable,
        }
        retry_entries.append(entry)

        if not schedulable:
            unretryable.append(job_id)

    schedule_status = (
        "all_unretryable"
        if retry_entries and len(unretryable) == len(retry_entries)
        else "scheduled"
    )

    return {
        "schedule_valid": True,
        "retry_entries": retry_entries,
        "unretryable_job_ids": sorted(unretryable),
        "schedule_status": schedule_status,
    }


def summarize_retry_schedule(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("schedule_valid") is not True:
        return {
            "summary_valid": False,
            "schedulable_count": 0,
            "unretryable_count": 0,
            "schedule_status": "invalid_input",
        }

    retry_entries = result.get("retry_entries", [])
    schedulable_count = len(
        [
            entry
            for entry in retry_entries
            if isinstance(entry, dict) and entry.get("schedulable") is True
        ]
    )
    unretryable_count = (
        len(result.get("unretryable_job_ids", []))
        if isinstance(result.get("unretryable_job_ids", []), list)
        else 0
    )

    return {
        "summary_valid": True,
        "schedulable_count": schedulable_count,
        "unretryable_count": unretryable_count,
        "schedule_status": result.get("schedule_status", "invalid_input"),
    }
