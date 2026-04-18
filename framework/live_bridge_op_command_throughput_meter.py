from typing import Any
def meter_command_throughput(meter_input):
    if not isinstance(meter_input, dict): return {"op_throughput_meter_status": "invalid"}
    if "throughput_value" not in meter_input: return {"op_throughput_meter_status": "invalid"}
    return {"op_throughput_meter_status": "metered", "throughput_value": meter_input.get("throughput_value")}
