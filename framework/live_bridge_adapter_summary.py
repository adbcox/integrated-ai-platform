from typing import Any

def summarize_adapter_layer(adapter_cp: Any, adapter_delivery_rollup: Any, adapter_report: Any) -> dict[str, Any]:
    if not isinstance(adapter_cp, dict) or not isinstance(adapter_delivery_rollup, dict) or not isinstance(adapter_report, dict):
        return {"adapter_summary_status": "failed"}
    cp_ok = adapter_cp.get("adapter_cp_status") == "operational"
    dr_ok = adapter_delivery_rollup.get("delivery_rollup_status") == "rolled_up"
    rpt_ok = adapter_report.get("adapter_layer_report_status") == "reported"
    if not cp_ok or not dr_ok or not rpt_ok:
        return {"adapter_summary_status": "failed"}
    return {
        "adapter_summary_status": "summarized",
        "adapter_cp_status": "operational",
    }
