from typing import Any
def integration_reporter(input_dict):
    if not isinstance(input_dict, dict): return {'exit_reporter_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_reporter_status': 'invalid'}
    return {'exit_reporter_status': 'complete'}
