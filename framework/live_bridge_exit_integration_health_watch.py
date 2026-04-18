from typing import Any
def integration_health_watch(input_dict):
    if not isinstance(input_dict, dict): return {'exit_watch_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_watch_status': 'invalid'}
    return {'exit_watch_status': 'complete'}
