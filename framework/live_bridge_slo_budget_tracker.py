from typing import Any

def track_slo_budget(slo_breach_detector: Any, budget_config: Any) -> dict[str, Any]:
    if not isinstance(slo_breach_detector, dict):
        return {"slo_budget_tracking_status": "not_tracked"}
    detect_ok = slo_breach_detector.get("slo_breach_detection_status") == "detected"
    if not detect_ok:
        return {"slo_budget_tracking_status": "not_tracked"}
    is_breach = slo_breach_detector.get("is_breach", False)
    return {
        "slo_budget_tracking_status": "tracked",
        "remaining_budget_pct": 0.0 if is_breach else budget_config.get("budget_pct", 100.0),
    }
