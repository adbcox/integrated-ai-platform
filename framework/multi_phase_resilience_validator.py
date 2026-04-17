from typing import Any


def validate_resilience_complete(
    resilience_audit: dict[str, Any],
    rate_limiter: dict[str, Any],
    load_balancer: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(resilience_audit, dict)
        or not isinstance(rate_limiter, dict)
        or not isinstance(load_balancer, dict)
    ):
        return {
            "resilience_validation_status": "invalid_input",
            "all_constraints_met": False,
            "resilience_validated": False,
        }

    audit_ok = resilience_audit.get("resilience_audit_status") == "passed"
    rate_limit_ok = rate_limiter.get("rate_limit_status") in ("allowed", "insufficient_tokens")
    load_ok = load_balancer.get("load_status") in ("balanced", "high_load", "overloaded")

    all_ok = audit_ok and rate_limit_ok and load_ok

    if not audit_ok:
        return {
            "resilience_validation_status": "audit_failed",
            "all_constraints_met": False,
            "resilience_validated": False,
        }

    if not all_ok:
        return {
            "resilience_validation_status": "incomplete",
            "all_constraints_met": False,
            "resilience_validated": False,
        }

    return {
        "resilience_validation_status": "valid",
        "all_constraints_met": True,
        "resilience_validated": True,
    }
