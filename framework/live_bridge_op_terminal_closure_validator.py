from typing import Any
def validator(input_dict):
    if not isinstance(input_dict, dict): return {'op_terminal_closure_validator_status': 'invalid'}
    if 'id' not in input_dict: return {'op_terminal_closure_validator_status': 'invalid'}
    return {'op_terminal_closure_validator_status': 'complete'}
