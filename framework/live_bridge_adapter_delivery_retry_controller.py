from typing import Any

def control_delivery_retry(watchdog: Any, retry_policy: Any, retry_state: Any) -> dict[str, Any]:
    if not isinstance(watchdog, dict) or not isinstance(retry_policy, dict):
        return {"delivery_retry_status": "failed"}
    max_attempts = retry_policy.get("max_attempts", 3)
    attempts = retry_state.get("attempts", 0) if isinstance(retry_state, dict) else 0
    if attempts >= max_attempts:
        return {"delivery_retry_status": "exhausted", "attempts": attempts}
    return {
        "delivery_retry_status": "retrying",
        "attempts": attempts + 1,
        "max_attempts": max_attempts,
    }
