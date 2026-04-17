from typing import Any
def resolve_capability_scope(binding: dict[str, Any], manifest: dict[str, Any], scope_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(binding, dict) or not isinstance(manifest, dict) or not isinstance(scope_config, dict):
        return {"scope_resolution_status": "invalid_input", "scope_env_id": None, "scope_manifest_id": None, "scope_level": None}
    b_ok = binding.get("capability_binding_status") == "bound"
    m_ok = manifest.get("manifest_status") == "built"
    if b_ok and m_ok:
        return {"scope_resolution_status": "resolved", "scope_env_id": binding.get("bound_env_id"), "scope_manifest_id": manifest.get("manifest_id"), "scope_level": scope_config.get("level", "standard")}
    return {"scope_resolution_status": "not_bound" if not b_ok else "no_manifest", "scope_env_id": None, "scope_manifest_id": None, "scope_level": None}
