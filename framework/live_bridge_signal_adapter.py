from typing import Any
def adapt_signal(routing: dict[str, Any], external_signal: dict[str, Any], adapter_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(routing, dict) or not isinstance(external_signal, dict) or not isinstance(adapter_config, dict):
        return {"signal_adaptation_status": "invalid_input", "adapted_signal_kind": None, "adapted_operation_id": None}
    r_ok = routing.get("autonomy_routing_status") == "routed"
    sig_ok = bool(external_signal.get("signal_kind"))
    if r_ok and sig_ok:
        return {"signal_adaptation_status": "adapted", "adapted_signal_kind": external_signal.get("signal_kind"), "adapted_operation_id": routing.get("routed_operation_id")}
    return {"signal_adaptation_status": "not_routed" if not r_ok else "no_signal", "adapted_signal_kind": None, "adapted_operation_id": None}
