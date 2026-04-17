from typing import Any


def audit_resilience(
    circuit_breaker: dict[str, Any],
    backpressure: dict[str, Any],
    budget_manager: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(circuit_breaker, dict)
        or not isinstance(backpressure, dict)
        or not isinstance(budget_manager, dict)
    ):
        return {
            "resilience_audit_status": "invalid_input",
            "components_healthy": 0,
            "resilience_ok": False,
        }

    circuit_ok = circuit_breaker.get("circuit_state") in ("closed", "half_open")
    backpressure_ok = backpressure.get("backpressure_status") in ("none", "partial", "applied")
    budget_ok = budget_manager.get("budget_status") in ("available", "last_attempt")

    healthy_count = sum(1 for x in [circuit_ok, backpressure_ok, budget_ok] if x)

    if circuit_breaker.get("circuit_state") == "open":
        return {
            "resilience_audit_status": "circuit_open",
            "components_healthy": healthy_count,
            "resilience_ok": False,
        }

    if budget_manager.get("budget_depleted") is True:
        return {
            "resilience_audit_status": "budget_depleted",
            "components_healthy": healthy_count,
            "resilience_ok": False,
        }

    if healthy_count == 3:
        return {
            "resilience_audit_status": "passed",
            "components_healthy": healthy_count,
            "resilience_ok": True,
        }

    return {
        "resilience_audit_status": "degraded",
        "components_healthy": healthy_count,
        "resilience_ok": False,
    }
