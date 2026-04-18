from typing import Any
def anomaly_detector(input_dict):
    if not isinstance(input_dict, dict): return {'exit_detector_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_detector_status': 'invalid'}
    return {'exit_detector_status': 'complete'}
