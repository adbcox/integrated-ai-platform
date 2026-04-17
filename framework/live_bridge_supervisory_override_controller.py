from typing import Any

def control_override(dispatch: dict, normalization: dict, override_config: dict) -> dict:
    if not isinstance(dispatch, dict) or not isinstance(normalization, dict) or not isinstance(override_config, dict):
        return {"override_status": "invalid_input"}
    d_ok = dispatch.get("directive_dispatch_status") == "dispatched"
    is_override = normalization.get("normalized_kind") == "override"
    if not d_ok:
        return {"override_status": "no_dispatch"}
    if not is_override:
        return {"override_status": "not_override"}
    return {
        "override_status": "applied",
        "override_directive_id": dispatch.get("dispatched_directive_id"),
        "override_target": override_config.get("target", "cycle"),
    }
