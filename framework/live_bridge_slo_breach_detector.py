from typing import Any

def detect_slo_breach(slo_tracker: Any, slo_descriptor: Any) -> dict[str, Any]:
    if not isinstance(slo_tracker, dict) or not isinstance(slo_descriptor, dict):
        return {"slo_breach_detection_status": "not_detected"}
    track_ok = slo_tracker.get("slo_tracking_status") == "tracked"
    desc_ok = slo_descriptor.get("slo_descriptor_status") == "described"
    if not track_ok or not desc_ok:
        return {"slo_breach_detection_status": "not_detected"}
    current = slo_tracker.get("current_pct", 0.0)
    target = slo_descriptor.get("target_pct", 0.0)
    is_breach = current < target
    return {
        "slo_breach_detection_status": "detected",
        "is_breach": is_breach,
    }
