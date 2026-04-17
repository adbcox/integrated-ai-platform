from typing import Any


def validate_end_state(
    completion_result: dict[str, Any],
    report_result: dict[str, Any],
    failure_result: dict[str, Any],
    trail_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(completion_result, dict)
        or not isinstance(report_result, dict)
        or not isinstance(failure_result, dict)
        or not isinstance(trail_result, dict)
    ):
        return {
            "validation_valid": False,
            "completion_consistent": False,
            "failure_consistent": False,
            "trail_consistent": False,
            "all_consistent": False,
            "inconsistencies": [],
            "end_state_status": "invalid_input",
        }

    completion_consistent = (
        completion_result.get("is_complete", False) is True
        and report_result.get("report_status") == "complete"
    )

    if failure_result.get("action") == "continue":
        failure_consistent = not completion_result.get("is_failed", False)
    else:
        failure_consistent = True

    if completion_result.get("is_complete", False):
        trail_consistent = trail_result.get("trail_status") in ("complete", "empty")
    else:
        trail_consistent = True

    inconsistencies = []
    if not completion_consistent:
        inconsistencies.append("completion_consistent")
    if not failure_consistent:
        inconsistencies.append("failure_consistent")
    if not trail_consistent:
        inconsistencies.append("trail_consistent")

    all_consistent = len(inconsistencies) == 0
    status = "valid" if all_consistent else "inconsistent"

    return {
        "validation_valid": True,
        "completion_consistent": completion_consistent,
        "failure_consistent": failure_consistent,
        "trail_consistent": trail_consistent,
        "all_consistent": all_consistent,
        "inconsistencies": inconsistencies,
        "end_state_status": status,
    }


def summarize_end_state(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("validation_valid") is not True:
        return {
            "summary_valid": False,
            "end_state_status": "invalid_input",
            "inconsistency_count": 0,
        }

    return {
        "summary_valid": True,
        "end_state_status": result.get("end_state_status", "invalid_input"),
        "inconsistency_count": (
            len(result.get("inconsistencies", []))
            if isinstance(result.get("inconsistencies", []), list)
            else 0
        ),
    }
