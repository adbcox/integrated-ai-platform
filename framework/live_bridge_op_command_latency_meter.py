from typing import Any
def meter_command_latency(meter_input):
    if not isinstance(meter_input, dict): return {"op_latency_meter_status": "invalid"}
    if "latency_ms" not in meter_input: return {"op_latency_meter_status": "invalid"}
    return {"op_latency_meter_status": "metered", "latency_ms": meter_input.get("latency_ms")}
