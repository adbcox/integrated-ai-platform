from typing import Any


def validate_exit_readiness(
    promotion_readiness: dict[str, Any],
    retention_validator: dict[str, Any],
    weakness_detector: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(promotion_readiness, dict)
        or not isinstance(retention_validator, dict)
        or not isinstance(weakness_detector, dict)
    ):
        return {
            "exit_readiness_status": "invalid_input",
            "exit_phase": None,
            "exit_signal": None,
        }

    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"
    rv_ok = retention_validator.get("retention_status") == "valid"
    wd_ok = weakness_detector.get("weakness_status") == "detected"
    all_ok = pr_ok and rv_ok and wd_ok

    if all_ok:
        return {
            "exit_readiness_status": "valid",
            "exit_phase": promotion_readiness.get("promotion_phase"),
            "exit_signal": "ready_for_exit",
        }

    if (pr_ok and rv_ok) or (pr_ok and wd_ok):
        return {
            "exit_readiness_status": "partial",
            "exit_phase": None,
            "exit_signal": None,
        }

    return {
        "exit_readiness_status": "failed",
        "exit_phase": None,
        "exit_signal": None,
    }
