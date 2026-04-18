from typing import Any

def describe_slo(slo_config: Any) -> dict[str, Any]:
    if not isinstance(slo_config, dict):
        return {"slo_descriptor_status": "not_described"}
    if not slo_config.get("slo_id") or slo_config.get("target_pct") is None:
        return {"slo_descriptor_status": "not_described"}
    return {
        "slo_descriptor_status": "described",
        "slo_id": slo_config.get("slo_id"),
        "target_pct": slo_config.get("target_pct"),
    }
