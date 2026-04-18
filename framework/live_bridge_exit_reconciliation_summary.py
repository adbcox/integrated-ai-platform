from typing import Any
def reconciliation_summary(input_dict):
    if not isinstance(input_dict, dict): return {'exit_summary_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_summary_status': 'invalid'}
    return {'exit_summary_status': 'complete'}
