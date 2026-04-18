from typing import Any
def slo_descriptor(input_dict):
    if not isinstance(input_dict, dict): return {'exit_descriptor_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_descriptor_status': 'invalid'}
    return {'exit_descriptor_status': 'complete'}
