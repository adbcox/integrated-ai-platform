from typing import Any

def flush_metric_buffer(metric_buffer: Any, flush_config: Any) -> dict[str, Any]:
    if not isinstance(metric_buffer, dict):
        return {"metric_flush_status": "not_flushed"}
    buf_ok = metric_buffer.get("metric_buffer_status") == "buffered"
    if not buf_ok:
        return {"metric_flush_status": "not_flushed"}
    return {
        "metric_flush_status": "flushed",
        "flushed_count": 1,
    }
