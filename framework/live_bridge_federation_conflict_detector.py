from typing import Any

def detect_conflict(cross_dispatch: dict[str, Any], peer_state: dict[str, Any], detector_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cross_dispatch, dict) or not isinstance(peer_state, dict) or not isinstance(detector_config, dict):
        return {"conflict_status": "invalid_input"}
    c_ok = cross_dispatch.get("cross_dispatch_status") == "dispatched"
    has_conflict = peer_state.get("conflict_signal", False)
    status = "detected" if (c_ok and has_conflict) else "none"
    return {"conflict_status": status}

