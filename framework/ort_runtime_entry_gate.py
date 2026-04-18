from typing import Any

def entry_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"ort_runtime_entry_gate_status": "invalid"}
    gov_ok = input_dict.get("governed_fed_seal_status") == "sealed"
    adp_ok = input_dict.get("adapter_layer_seal_status") == "sealed"
    obs_ok = input_dict.get("obs_layer_seal_status") == "sealed"
    rec_ok = input_dict.get("reconciliation_status") == "sealed"
    if gov_ok and adp_ok and obs_ok and rec_ok:
        return {"ort_runtime_entry_gate_status": "open"}
    return {"ort_runtime_entry_gate_status": "invalid"}
