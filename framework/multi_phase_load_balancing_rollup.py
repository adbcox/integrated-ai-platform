from typing import Any


def rollup_load_balancing(
    phase_rebalancer: dict[str, Any],
    rate_limiter: dict[str, Any],
    resilience_reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase_rebalancer, dict)
        or not isinstance(rate_limiter, dict)
        or not isinstance(resilience_reporter, dict)
    ):
        return {
            "load_balancing_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    rebalance_ok = phase_rebalancer.get("rebalance_status") in ("redistributed", "no_rebalance_needed")
    rate_limit_ok = rate_limiter.get("rate_limit_status") in ("allowed", "insufficient_tokens", "limit_reached")
    reporter_ok = resilience_reporter.get("resilience_report_status") == "complete"

    all_complete = rebalance_ok and rate_limit_ok and reporter_ok

    if not all_complete:
        count = sum(
            1
            for ok in [rebalance_ok, rate_limit_ok, reporter_ok]
            if ok
        )
        return {
            "load_balancing_rollup_status": "incomplete_source",
            "rollup_phase": None,
            "operations_complete": count,
        }

    return {
        "load_balancing_rollup_status": "rolled_up",
        "rollup_phase": resilience_reporter.get("report_phase"),
        "operations_complete": 3,
    }
