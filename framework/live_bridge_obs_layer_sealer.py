from typing import Any

def seal_obs_layer(obs_layer_finalization: Any, obs_layer_report: Any) -> dict[str, Any]:
    if not isinstance(obs_layer_finalization, dict) or not isinstance(obs_layer_report, dict):
        return {"obs_layer_seal_status": "not_sealed"}
    final_ok = obs_layer_finalization.get("obs_layer_finalization_status") == "finalized"
    report_ok = obs_layer_report.get("obs_layer_report_status") == "reported"
    if not final_ok or not report_ok:
        return {"obs_layer_seal_status": "not_sealed"}
    return {
        "obs_layer_seal_status": "sealed",
    }
