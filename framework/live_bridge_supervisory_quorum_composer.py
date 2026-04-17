from typing import Any

def compose_quorum(matrix: dict, quorum_policy: dict, composer_config: dict) -> dict:
    if not isinstance(matrix, dict) or not isinstance(quorum_policy, dict) or not isinstance(composer_config, dict):
        return {"quorum_composition_status": "invalid_input"}
    m_ok = matrix.get("authority_matrix_status") == "built"
    min_members = int(quorum_policy.get("min_members", 2))
    available = int(quorum_policy.get("available", 0))
    if not m_ok:
        return {"quorum_composition_status": "no_matrix"}
    if available < min_members:
        return {"quorum_composition_status": "insufficient_members"}
    return {
        "quorum_composition_status": "composed",
        "quorum_size": available,
        "quorum_minimum": min_members,
        "quorum_id": composer_config.get("quorum_id", "qum-0001"),
    }
