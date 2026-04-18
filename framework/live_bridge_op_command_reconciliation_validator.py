from typing import Any
def validate_command_reconciliation(validation):
    if not isinstance(validation, dict): return {"op_reconciliation_validation_status": "invalid"}
    if validation.get("op_reconciliation_execute_status") != "executed": return {"op_reconciliation_validation_status": "invalid"}
    return {"op_reconciliation_validation_status": "valid", "reconciliation_id": validation.get("reconciliation_id")}
