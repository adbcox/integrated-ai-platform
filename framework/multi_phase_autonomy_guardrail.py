from typing import Any


def check_autonomy_guardrails(
    execution_arbitration: dict[str, Any],
    watchdog: dict[str, Any],
    guardrail_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(execution_arbitration, dict)
        or not isinstance(watchdog, dict)
        or not isinstance(guardrail_policy, dict)
    ):
        return {
            "guardrail_status": "invalid_input",
            "guardrail_phase": None,
            "block_reason": None,
        }

    exec_ok = execution_arbitration.get("execution_arbitration_status") == "authorized"
    watchdog_clear = watchdog.get("watchdog_status") == "clear"
    watchdog_alert = watchdog.get("watchdog_status") in ("alert", "critical")

    if exec_ok and watchdog_clear:
        return {
            "guardrail_status": "clear",
            "guardrail_phase": execution_arbitration.get("authorized_phase"),
            "block_reason": None,
        }

    if exec_ok and watchdog_alert:
        return {
            "guardrail_status": "blocked",
            "guardrail_phase": None,
            "block_reason": watchdog.get("watchdog_status"),
        }

    if not exec_ok:
        return {
            "guardrail_status": "no_arbitration",
            "guardrail_phase": None,
            "block_reason": None,
        }

    return {
        "guardrail_status": "invalid_input",
        "guardrail_phase": None,
        "block_reason": None,
    }
