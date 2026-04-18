from typing import Any
def delivery_retry_validator(input_dict):
    if not isinstance(input_dict, dict): return {'exit_validator_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_validator_status': 'invalid'}
    return {'exit_validator_status': 'complete'}
