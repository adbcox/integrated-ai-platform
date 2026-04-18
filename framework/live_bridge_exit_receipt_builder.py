from typing import Any
def receipt_builder(input_dict):
    if not isinstance(input_dict, dict): return {'exit_builder_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_builder_status': 'invalid'}
    return {'exit_builder_status': 'complete'}
