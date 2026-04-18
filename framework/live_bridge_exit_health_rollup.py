from typing import Any
def health_rollup(input_dict):
    if not isinstance(input_dict, dict): return {'exit_rollup_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_rollup_status': 'invalid'}
    return {'exit_rollup_status': 'complete'}
