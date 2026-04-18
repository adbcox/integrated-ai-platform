from typing import Any
def attestation_summary(input_dict):
    if not isinstance(input_dict, dict): return {'op_terminal_closure_attestation_summary_status': 'invalid'}
    if 'id' not in input_dict: return {'op_terminal_closure_attestation_summary_status': 'invalid'}
    return {'op_terminal_closure_attestation_summary_status': 'complete'}
