from typing import Any


def rollup_orchestration_consistency(
    end_state_result: dict[str, Any],
    trail_result: dict[str, Any],
    completion_result: dict[str, Any],
    readiness_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(end_state_result, dict)
        or not isinstance(trail_result, dict)
        or not isinstance(completion_result, dict)
        or not isinstance(readiness_result, dict)
    ):
        return {
            "rollup_valid": False,
            "end_state_consistent": False,
            "trail_complete": False,
            "completion_detected": False,
            "orchestration_ready": False,
            "all_consistent": False,
            "failed_checks": [],
            "rollup_status": "invalid_input",
        }

    end_state_consistent = end_state_result.get("end_state_status") == "valid"
    trail_complete = trail_result.get("trail_status") in ("complete", "empty")
    completion_detected = completion_result.get("is_complete", False) is True
    orchestration_ready = readiness_result.get("overall_ready", False) is True

    failed_checks = []

    if not end_state_consistent:
        failed_checks.append("end_state_consistent")
    if not trail_complete:
        failed_checks.append("trail_complete")
    if not completion_detected:
        failed_checks.append("completion_detected")
    if not orchestration_ready:
        failed_checks.append("orchestration_ready")

    all_consistent = len(failed_checks) == 0

    return {
        "rollup_valid": True,
        "end_state_consistent": end_state_consistent,
        "trail_complete": trail_complete,
        "completion_detected": completion_detected,
        "orchestration_ready": orchestration_ready,
        "all_consistent": all_consistent,
        "failed_checks": failed_checks,
        "rollup_status": "consistent" if all_consistent else "inconsistent",
    }


def summarize_consistency_rollup(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("rollup_valid") is not True:
        return {
            "summary_valid": False,
            "rollup_status": "invalid_input",
            "failed_check_count": 0,
        }

    return {
        "summary_valid": True,
        "rollup_status": result.get("rollup_status", "invalid_input"),
        "failed_check_count": (
            len(result.get("failed_checks", []))
            if isinstance(result.get("failed_checks", []), list)
            else 0
        ),
    }
