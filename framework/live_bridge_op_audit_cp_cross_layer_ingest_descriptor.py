from typing import Any

def describe_ingest(ingest_input):
    if not isinstance(ingest_input, dict): return {'op_audit_cp_ingest_descriptor_status': 'invalid'}
    if 'ingest_id' not in ingest_input: return {'op_audit_cp_ingest_descriptor_status': 'invalid'}
    return {'op_audit_cp_ingest_descriptor_status': 'described'}
