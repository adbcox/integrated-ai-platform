from typing import Any
def seal_audit_cp_layer(seal_input):
    if not isinstance(seal_input, dict): return {"op_audit_cp_layer_seal_status": "invalid"}
    if seal_input.get("op_audit_cp_completion_report_status") != "complete": return {"op_audit_cp_layer_seal_status": "invalid"}
    if seal_input.get("op_audit_cp_layer_finalization_status") != "finalized": return {"op_audit_cp_layer_seal_status": "invalid"}
    return {"op_audit_cp_layer_seal_status": "sealed"}
