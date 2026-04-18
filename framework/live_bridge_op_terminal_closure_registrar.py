from typing import Any
def registrar(input_dict):
    if not isinstance(input_dict, dict): return {'op_terminal_closure_registrar_status': 'invalid'}
    if 'id' not in input_dict: return {'op_terminal_closure_registrar_status': 'invalid'}
    return {'op_terminal_closure_registrar_status': 'complete'}
