from typing import Any

def finalize_obs_layer(obs_layer_gate: Any) -> dict[str, Any]:
    if not isinstance(obs_layer_gate, dict):
        return {"obs_layer_finalization_status": "not_finalized"}
    gate_ok = obs_layer_gate.get("obs_layer_gate_status") == "open"
    if not gate_ok:
        return {"obs_layer_finalization_status": "not_finalized"}
    return {
        "obs_layer_finalization_status": "finalized",
    }
