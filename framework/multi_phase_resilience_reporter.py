from typing import Any


def report_resilience(
    validation: dict[str, Any],
    phase_rebalancer: dict[str, Any],
    load_balancer: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(phase_rebalancer, dict)
        or not isinstance(load_balancer, dict)
    ):
        return {
            "resilience_report_status": "invalid_input",
            "report_phase": None,
            "load_balanced": False,
            "resilience_reported": False,
        }

    if validation.get("resilience_validation_status") != "valid":
        return {
            "resilience_report_status": "validation_failed",
            "report_phase": None,
            "load_balanced": False,
            "resilience_reported": False,
        }

    load_status = load_balancer.get("load_status")
    balanced = load_status == "balanced"

    if phase_rebalancer.get("rebalance_status") not in ("redistributed", "no_rebalance_needed"):
        return {
            "resilience_report_status": "rebalance_incomplete",
            "report_phase": None,
            "load_balanced": balanced,
            "resilience_reported": False,
        }

    return {
        "resilience_report_status": "complete",
        "report_phase": phase_rebalancer.get("phases_redistributed", 0),
        "load_balanced": balanced,
        "resilience_reported": True,
    }
