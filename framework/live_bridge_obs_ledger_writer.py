from typing import Any

def write_obs_to_ledger(telemetry_sink_confirmation_receipt: Any, ledger_config: Any) -> dict[str, Any]:
    if not isinstance(telemetry_sink_confirmation_receipt, dict):
        return {"obs_ledger_write_status": "not_written"}
    conf_ok = telemetry_sink_confirmation_receipt.get("telemetry_sink_confirmation_receipt_status") == "received"
    if not conf_ok:
        return {"obs_ledger_write_status": "not_written"}
    return {
        "obs_ledger_write_status": "written",
        "ledger_entry_count": 1,
    }
