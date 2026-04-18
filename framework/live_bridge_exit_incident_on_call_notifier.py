from typing import Any
def incident_on_call_notifier(input_dict):
    if not isinstance(input_dict, dict): return {'exit_notifier_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_notifier_status': 'invalid'}
    return {'exit_notifier_status': 'complete'}
