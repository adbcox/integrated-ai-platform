from typing import Any

def create_telemetry_sink_manifest(telemetry_config: Any) -> dict[str, Any]:
    if not isinstance(telemetry_config, dict):
        return {"telemetry_sink_manifest_status": "not_created"}
    if not telemetry_config.get("sink_id"):
        return {"telemetry_sink_manifest_status": "not_created"}
    return {
        "telemetry_sink_manifest_status": "created",
        "sink_id": telemetry_config.get("sink_id"),
        "endpoint": telemetry_config.get("endpoint", ""),
    }
