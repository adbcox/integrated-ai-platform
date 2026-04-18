from typing import Any

def rollup_metrics(metric_flush: Any) -> dict[str, Any]:
    if not isinstance(metric_flush, dict):
        return {"metric_rollup_status": "not_rolled_up"}
    flush_ok = metric_flush.get("metric_flush_status") == "flushed"
    if not flush_ok:
        return {"metric_rollup_status": "not_rolled_up"}
    return {
        "metric_rollup_status": "rolled_up",
    }
