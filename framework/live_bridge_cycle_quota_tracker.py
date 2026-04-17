from typing import Any

def track_quota(admission: dict[str, Any], quota_config: dict[str, Any], counter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(admission, dict) or not isinstance(quota_config, dict) or not isinstance(counter, dict):
        return {"quota_tracker_status": "invalid_input", "quota_used": 0, "quota_remaining": 0}
    a_ok = admission.get("admission_status") == "admitted"
    used = int(counter.get("used", 0)) if isinstance(counter, dict) else 0
    quota = int(quota_config.get("quota", 100)) if isinstance(quota_config, dict) else 100
    if used >= quota:
        return {"quota_tracker_status": "at_limit", "quota_used": used, "quota_remaining": 0}
    return {"quota_tracker_status": "under_limit", "quota_used": used + 1 if a_ok else used, "quota_remaining": max(0, quota - used - (1 if a_ok else 0))} if used < quota else {"quota_tracker_status": "invalid_input", "quota_used": 0, "quota_remaining": 0}
