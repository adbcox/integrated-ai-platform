from typing import Any
def integration_control_plane(input_dict):
    if not isinstance(input_dict, dict): return {'exit_plane_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_plane_status': 'invalid'}
    return {'exit_plane_status': 'complete'}
