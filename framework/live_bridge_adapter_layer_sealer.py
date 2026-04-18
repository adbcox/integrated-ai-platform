from typing import Any

def seal_adapter_layer(layer_gate: Any, adapter_cp: Any, sealer_config: Any) -> dict[str, Any]:
    if not isinstance(layer_gate, dict) or not isinstance(adapter_cp, dict):
        return {"adapter_layer_seal_status": "not_sealed"}
    g_ok = layer_gate.get("adapter_layer_gate_status") == "open"
    cp_ok = adapter_cp.get("adapter_cp_status") == "operational"
    if not g_ok or not cp_ok:
        return {"adapter_layer_seal_status": "not_sealed"}
    return {
        "adapter_layer_seal_status": "sealed",
    }
