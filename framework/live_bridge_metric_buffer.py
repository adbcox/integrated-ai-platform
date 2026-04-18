from typing import Any

def buffer_metric(metric_normalization: Any, buffer_config: Any) -> dict[str, Any]:
    if not isinstance(metric_normalization, dict):
        return {"metric_buffer_status": "not_buffered"}
    norm_ok = metric_normalization.get("metric_normalization_status") == "normalized"
    if not norm_ok:
        return {"metric_buffer_status": "not_buffered"}
    return {
        "metric_buffer_status": "buffered",
        "buffer_size": buffer_config.get("buffer_size", 0),
    }
