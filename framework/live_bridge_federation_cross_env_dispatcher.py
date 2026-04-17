from typing import Any

def dispatch_cross_env(workload_split: dict[str, Any], dispatch: dict[str, Any], dispatcher_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(workload_split, dict) or not isinstance(dispatch, dict) or not isinstance(dispatcher_config, dict):
        return {"cross_dispatch_status": "invalid_input", "cross_dispatch_id": None}
    w_ok = workload_split.get("workload_split_status") == "split"
    d_ok = dispatch.get("dispatch_status") == "dispatched"
    if not w_ok:
        return {"cross_dispatch_status": "workload_not_split", "cross_dispatch_id": None}
    return {"cross_dispatch_status": "dispatched", "cross_dispatch_id": dispatcher_config.get("cross_dispatch_id", "xd-0001")} if w_ok and d_ok else {"cross_dispatch_status": "dispatch_failed", "cross_dispatch_id": None}

