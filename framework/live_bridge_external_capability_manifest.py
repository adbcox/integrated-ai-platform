from typing import Any
def build_external_capability_manifest(scope_resolution: dict[str, Any], capability_binding: dict[str, Any], manifest_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(scope_resolution, dict) or not isinstance(capability_binding, dict) or not isinstance(manifest_config, dict):
        return {"external_manifest_status": "invalid_input", "external_manifest_env_id": None, "external_manifest_id": None}
    sr_ok = scope_resolution.get("scope_resolution_status") == "resolved"
    cb_ok = capability_binding.get("capability_binding_status") == "bound"
    if sr_ok and cb_ok:
        return {"external_manifest_status": "built", "external_manifest_env_id": capability_binding.get("bound_env_id"), "external_manifest_id": manifest_config.get("external_manifest_id", "ext-man-0001")}
    return {"external_manifest_status": "no_scope" if not sr_ok else "not_bound", "external_manifest_env_id": None, "external_manifest_id": None}
