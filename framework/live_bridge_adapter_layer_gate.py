from typing import Any

def gate_adapter_layer(adapter_summary: Any, adapter_health: Any, governed_fed_seal: Any) -> dict[str, Any]:
    if not isinstance(adapter_summary, dict) or not isinstance(adapter_health, dict) or not isinstance(governed_fed_seal, dict):
        return {"adapter_layer_gate_status": "closed"}
    s_ok = adapter_summary.get("adapter_summary_status") == "summarized"
    h_ok = adapter_health.get("adapter_health_status") == "green"
    seal_ok = governed_fed_seal.get("governed_fed_seal_status") == "sealed"
    if not s_ok or not h_ok or not seal_ok:
        return {"adapter_layer_gate_status": "closed"}
    return {
        "adapter_layer_gate_status": "open",
    }
