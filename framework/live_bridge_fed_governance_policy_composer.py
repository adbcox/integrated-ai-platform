from typing import Any

def compose_fed_policy(authority_matrix: dict, boundary_policy: dict, composer_config: dict) -> dict:
    if not isinstance(authority_matrix, dict) or not isinstance(boundary_policy, dict) or not isinstance(composer_config, dict):
        return {"fed_policy_composition_status": "invalid_input"}
    am_ok = authority_matrix.get("authority_matrix_status") == "built"
    bp_ok = boundary_policy.get("boundary_policy_status") == "resolved"
    if not am_ok:
        return {"fed_policy_composition_status": "no_matrix"}
    if not bp_ok:
        return {"fed_policy_composition_status": "no_boundary"}
    return {
        "fed_policy_composition_status": "composed",
        "fed_policy_id": composer_config.get("fed_policy_id", "fpol-0001"),
        "fed_policy_source_boundary_id": boundary_policy.get("policy_id"),
        "fed_policy_matrix_id": authority_matrix.get("matrix_id"),
    }
