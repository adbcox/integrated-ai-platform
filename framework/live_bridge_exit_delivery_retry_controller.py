from typing import Any
def delivery_retry_controller(input_dict):
    if not isinstance(input_dict, dict): return {'exit_controller_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_controller_status': 'invalid'}
    return {'exit_controller_status': 'complete'}
