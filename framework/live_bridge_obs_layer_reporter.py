from typing import Any

def report_obs_layer(obs_layer_validation: Any) -> dict[str, Any]:
    if not isinstance(obs_layer_validation, dict):
        return {"obs_layer_report_status": "not_reported"}
    valid_ok = obs_layer_validation.get("obs_layer_validation_status") == "valid"
    if not valid_ok:
        return {"obs_layer_report_status": "not_reported"}
    return {
        "obs_layer_report_status": "reported",
    }
