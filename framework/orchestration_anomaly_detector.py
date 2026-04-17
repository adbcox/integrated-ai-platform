from typing import Any


def detect_orchestration_anomalies(
    throughput_result: dict[str, Any],
    blocking_result: dict[str, Any],
    retry_result: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(throughput_result, dict)
        or not isinstance(blocking_result, dict)
        or not isinstance(retry_result, dict)
        or not isinstance(thresholds, dict)
    ):
        return {
            "detection_valid": False,
            "throughput_anomaly": False,
            "blocking_anomaly": False,
            "retry_anomaly": False,
            "anomaly_count": 0,
            "anomaly_types": [],
            "anomaly_status": "invalid_input",
        }

    throughput_anomaly = (
        float(throughput_result.get("mean_throughput", 0.0))
        < float(thresholds.get("min_throughput", 0.0))
    )
    blocking_anomaly = (
        blocking_result.get("blocking_type") in ("deadlock", "stall")
        and bool(thresholds.get("block_is_anomaly", False))
    )

    retry_entries = retry_result.get("retry_entries", [])
    if not isinstance(retry_entries, list):
        retry_entries = []

    retry_anomaly = len(retry_entries) > int(
        thresholds.get("max_retry_entries", 999)
    )

    anomaly_types = []
    if throughput_anomaly:
        anomaly_types.append("throughput")
    if blocking_anomaly:
        anomaly_types.append("blocking")
    if retry_anomaly:
        anomaly_types.append("retry")

    anomaly_count = len(anomaly_types)

    if anomaly_count == 0:
        status = "clean"
    elif anomaly_count == 1:
        status = "warning"
    else:
        status = "critical"

    return {
        "detection_valid": True,
        "throughput_anomaly": throughput_anomaly,
        "blocking_anomaly": blocking_anomaly,
        "retry_anomaly": retry_anomaly,
        "anomaly_count": anomaly_count,
        "anomaly_types": anomaly_types,
        "anomaly_status": status,
    }


def summarize_anomaly_detection(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("detection_valid") is not True:
        return {
            "summary_valid": False,
            "anomaly_status": "invalid_input",
            "anomaly_count": 0,
        }

    return {
        "summary_valid": True,
        "anomaly_status": result.get("anomaly_status", "invalid_input"),
        "anomaly_count": int(result.get("anomaly_count", 0)),
    }
