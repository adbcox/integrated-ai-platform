from typing import Any
def health_rollup(input_dict):
    if not isinstance(input_dict, dict): return {'op_terminal_closure_health_rollup_status': 'invalid'}
    if 'id' not in input_dict: return {'op_terminal_closure_health_rollup_status': 'invalid'}
    return {'op_terminal_closure_health_rollup_status': 'complete'}
