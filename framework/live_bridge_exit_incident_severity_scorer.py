from typing import Any
def incident_severity_scorer(input_dict):
    if not isinstance(input_dict, dict): return {'exit_scorer_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_scorer_status': 'invalid'}
    return {'exit_scorer_status': 'complete'}
