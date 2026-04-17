from typing import Any

def meter_latency(watchdog: dict[str, Any], acknowledgement: dict[str, Any], meter_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(watchdog, dict) or not isinstance(acknowledgement, dict) or not isinstance(meter_config, dict):
        return {"latency_status": "invalid_input", "latency_operation_id": None, "latency_ms": 0}
    w_ok = watchdog.get("watchdog_status") == "ok"
    w_timeout = watchdog.get("watchdog_status") == "timed_out"
    a_ok = acknowledgement.get("acknowledgement_status") == "acknowledged"
    if w_timeout:
        return {"latency_status": "timed_out", "latency_operation_id": None, "latency_ms": 0}
    if w_ok and not a_ok:
        return {"latency_status": "not_acknowledged", "latency_operation_id": None, "latency_ms": 0}
    return {"latency_status": "measured", "latency_operation_id": acknowledgement.get("acked_operation_id"), "latency_ms": int(watchdog.get("elapsed_seconds", 0)) * 1000} if w_ok and a_ok else {"latency_status": "invalid_input", "latency_operation_id": None, "latency_ms": 0}
