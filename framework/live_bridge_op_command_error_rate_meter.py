from typing import Any
def meter_command_error_rate(meter_input):
    if not isinstance(meter_input, dict): return {"op_error_rate_meter_status": "invalid"}
    if "error_rate" not in meter_input: return {"op_error_rate_meter_status": "invalid"}
    return {"op_error_rate_meter_status": "metered", "error_rate": meter_input.get("error_rate")}
