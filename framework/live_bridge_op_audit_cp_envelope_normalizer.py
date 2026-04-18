from typing import Any
def envelope_normalizer(input_dict):
    if not isinstance(input_dict, dict): return {'op_audit_cp_normalizer_status': 'invalid'}
    if 'id' not in input_dict: return {'op_audit_cp_normalizer_status': 'invalid'}
    return {'op_audit_cp_normalizer_status': 'complete'}
