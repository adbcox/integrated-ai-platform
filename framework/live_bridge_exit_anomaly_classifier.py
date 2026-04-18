from typing import Any
def anomaly_classifier(input_dict):
    if not isinstance(input_dict, dict): return {'exit_classifier_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_classifier_status': 'invalid'}
    return {'exit_classifier_status': 'complete'}
