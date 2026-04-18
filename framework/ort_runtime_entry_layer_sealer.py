from typing import Any

def entry_layer_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_entry_seal_status": "invalid"}
    if input_dict.get("ort_runtime_entry_finalization_status") != "finalized":
        return {"runtime_entry_seal_status": "invalid"}
    if input_dict.get("ort_runtime_entry_completion_report_status") != "complete":
        return {"runtime_entry_seal_status": "invalid"}
    return {"runtime_entry_seal_status": "sealed"}
