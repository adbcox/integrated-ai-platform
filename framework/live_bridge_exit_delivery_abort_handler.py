from typing import Any
def delivery_abort_handler(input_dict):
    if not isinstance(input_dict, dict): return {'exit_handler_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_handler_status': 'invalid'}
    return {'exit_handler_status': 'complete'}
