from typing import Any

def gate_obs_layer(obs_summary: Any, obs_health: Any, adapter_seal: Any) -> dict[str, Any]:
    if not isinstance(obs_summary, dict) or not isinstance(obs_health, dict) or not isinstance(adapter_seal, dict):
        return {"obs_layer_gate_status": "closed"}
    summary_ok = obs_summary.get("obs_summary_status") == "summarized"
    health_ok = obs_health.get("obs_health_status") == "green"
    seal_ok = adapter_seal.get("adapter_layer_seal_status") == "sealed"
    if not summary_ok or not health_ok or not seal_ok:
        return {"obs_layer_gate_status": "closed"}
    return {
        "obs_layer_gate_status": "open",
    }
