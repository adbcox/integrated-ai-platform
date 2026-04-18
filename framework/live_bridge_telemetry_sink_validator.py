from typing import Any

def validate_telemetry_sink(telemetry_sink_manifest: Any) -> dict[str, Any]:
    if not isinstance(telemetry_sink_manifest, dict):
        return {"telemetry_sink_validation_status": "not_validated"}
    manifest_ok = telemetry_sink_manifest.get("telemetry_sink_manifest_status") == "created"
    if not manifest_ok:
        return {"telemetry_sink_validation_status": "not_validated"}
    return {
        "telemetry_sink_validation_status": "valid",
    }
