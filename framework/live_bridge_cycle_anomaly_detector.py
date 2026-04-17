from typing import Any

def detect_cycle_anomaly(cycle_health: dict[str, Any], latency: dict[str, Any], throughput: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle_health, dict) or not isinstance(latency, dict) or not isinstance(throughput, dict):
        return {"anomaly_status": "invalid_input", "anomaly_kind": "none", "anomaly_count": 0}
    ch_red = cycle_health.get("cycle_health_watch_status") == "red"
    lat_timed_out = latency.get("latency_status") == "timed_out"
    tp_missing = throughput.get("throughput_status") != "measured"
    anomalous = ch_red or lat_timed_out or tp_missing
    if anomalous:
        kind = "health_red" if ch_red else ("timeout" if lat_timed_out else ("throughput_missing" if tp_missing else "none"))
        return {"anomaly_status": "detected", "anomaly_kind": kind, "anomaly_count": int(ch_red) + int(lat_timed_out) + int(tp_missing)}
    return {"anomaly_status": "none", "anomaly_kind": "none", "anomaly_count": 0}
