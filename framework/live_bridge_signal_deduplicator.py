from typing import Any

def deduplicate_signals(signal_correlation: Any, dedup_config: Any) -> dict[str, Any]:
    if not isinstance(signal_correlation, dict):
        return {"signal_deduplication_status": "not_deduplicated"}
    corr_ok = signal_correlation.get("signal_correlation_status") == "correlated"
    if not corr_ok:
        return {"signal_deduplication_status": "not_deduplicated"}
    return {
        "signal_deduplication_status": "deduplicated",
        "unique_signal_count": 1,
    }
