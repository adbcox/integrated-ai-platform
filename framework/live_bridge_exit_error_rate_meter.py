from typing import Any
def error_rate_meter(input_dict):
    if not isinstance(input_dict, dict): return {'exit_meter_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_meter_status': 'invalid'}
    return {'exit_meter_status': 'complete'}
