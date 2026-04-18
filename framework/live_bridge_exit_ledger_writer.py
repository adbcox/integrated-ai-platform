from typing import Any
def ledger_writer(input_dict):
    if not isinstance(input_dict, dict): return {'exit_writer_status': 'invalid'}
    if 'id' not in input_dict: return {'exit_writer_status': 'invalid'}
    return {'exit_writer_status': 'complete'}
