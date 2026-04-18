from typing import Any
def receipt_signer(input_dict):
    if not isinstance(input_dict, dict): return {'exit_signer_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_signer_status': 'invalid'}
    return {'exit_signer_status': 'complete'}
