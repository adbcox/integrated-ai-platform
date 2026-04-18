from typing import Any
def reconciliation_planner(input_dict):
    if not isinstance(input_dict, dict): return {'exit_planner_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_planner_status': 'invalid'}
    return {'exit_planner_status': 'complete'}
