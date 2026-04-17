from typing import Any


def audit_optimization(
    schedule_adapt: dict[str, Any],
    predictive_balance: dict[str, Any],
    closed_loop: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(schedule_adapt, dict)
        or not isinstance(predictive_balance, dict)
        or not isinstance(closed_loop, dict)
    ):
        return {
            "optimization_audit_status": "invalid_input",
            "ok_count": 0,
            "audit_phase": None,
        }

    schedule_ok = schedule_adapt.get("adaptation_status") == "adapted"
    balance_ok = predictive_balance.get("balancing_status") in (
        "rebalanced",
        "holding",
    )
    loop_ok = closed_loop.get("loop_status") == "closed"

    all_ok = schedule_ok and balance_ok and loop_ok
    any_ok = schedule_ok or balance_ok or loop_ok
    ok_count = sum([schedule_ok, balance_ok, loop_ok])

    if all_ok:
        return {
            "optimization_audit_status": "passed",
            "ok_count": ok_count,
            "audit_phase": schedule_adapt.get("adapted_phase"),
        }

    if any_ok:
        return {
            "optimization_audit_status": "degraded",
            "ok_count": ok_count,
            "audit_phase": None,
        }

    return {
        "optimization_audit_status": "failed",
        "ok_count": ok_count,
        "audit_phase": None,
    }
