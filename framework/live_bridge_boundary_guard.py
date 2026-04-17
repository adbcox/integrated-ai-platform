from typing import Any
def guard_boundary(scope_resolution: dict[str, Any], promotion_attestation: dict[str, Any], guard_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(scope_resolution, dict) or not isinstance(promotion_attestation, dict) or not isinstance(guard_config, dict):
        return {"boundary_guard_status": "invalid_input", "guard_env_id": None, "guard_level": None}
    sr_ok = scope_resolution.get("scope_resolution_status") == "resolved"
    pa_ok = promotion_attestation.get("promotion_attestation_status") == "attested"
    if sr_ok and pa_ok:
        return {"boundary_guard_status": "armed", "guard_env_id": scope_resolution.get("scope_env_id"), "guard_level": guard_config.get("level", "strict")}
    return {"boundary_guard_status": "no_scope" if not sr_ok else "not_attested", "guard_env_id": None, "guard_level": None}
