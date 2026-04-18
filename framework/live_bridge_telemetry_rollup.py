from typing import Any

def rollup_telemetry(telemetry_sink_confirmation_receipt: Any) -> dict[str, Any]:
    if not isinstance(telemetry_sink_confirmation_receipt, dict):
        return {"telemetry_rollup_status": "not_rolled_up"}
    conf_ok = telemetry_sink_confirmation_receipt.get("telemetry_sink_confirmation_receipt_status") == "received"
    if not conf_ok:
        return {"telemetry_rollup_status": "not_rolled_up"}
    return {
        "telemetry_rollup_status": "rolled_up",
    }
