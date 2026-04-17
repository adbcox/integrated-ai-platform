from typing import Any

def rollup_supervisory(role: dict, matrix: dict, quorum_validation: dict) -> dict:
    if not isinstance(role, dict) or not isinstance(matrix, dict) or not isinstance(quorum_validation, dict):
        return {"supervisory_rollup_status": "invalid_input"}
    all_complete = (
        role.get("role_assignment_status") == "assigned" and
        matrix.get("authority_matrix_status") == "built" and
        quorum_validation.get("quorum_validation_status") == "valid"
    )
    if all_complete:
        return {
            "supervisory_rollup_status": "rolled_up",
            "rollup_role_id": role.get("role_id"),
            "operations_complete": 3,
        }
    return {"supervisory_rollup_status": "incomplete_source", "operations_complete": 0}
