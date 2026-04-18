from typing import Any
def slo_tracker(input_dict):
    if not isinstance(input_dict, dict): return {'exit_tracker_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_tracker_status': 'invalid'}
    return {'exit_tracker_status': 'complete'}
