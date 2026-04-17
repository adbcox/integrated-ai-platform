from typing import Any

def control_rollback(dispatch: dict, normalization: dict, rollback_config: dict) -> dict:
    if not isinstance(dispatch, dict) or not isinstance(normalization, dict) or not isinstance(rollback_config, dict):
        return {"rollback_status": "invalid_input"}
    d_ok = dispatch.get("directive_dispatch_status") == "dispatched"
    is_rollback = normalization.get("normalized_kind") == "rollback"
    if not d_ok:
        return {"rollback_status": "no_dispatch"}
    if not is_rollback:
        return {"rollback_status": "not_rollback"}
    return {
        "rollback_status": "applied",
        "rollback_directive_id": dispatch.get("dispatched_directive_id"),
        "rollback_target_tick": rollback_config.get("target_tick", 0),
    }
