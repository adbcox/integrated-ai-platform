from typing import Any

def throttle_signal_emission(signal_deduplication: Any, throttle_config: Any) -> dict[str, Any]:
    if not isinstance(signal_deduplication, dict):
        return {"signal_throttling_status": "not_throttled"}
    dedup_ok = signal_deduplication.get("signal_deduplication_status") == "deduplicated"
    if not dedup_ok:
        return {"signal_throttling_status": "not_throttled"}
    return {
        "signal_throttling_status": "throttled",
        "emission_rate_hz": throttle_config.get("emission_rate_hz", 1.0),
    }
