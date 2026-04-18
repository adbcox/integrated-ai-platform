from typing import Any

def register_ingest(descriptor):
    if not isinstance(descriptor, dict): return {'op_audit_cp_ingest_registration_status': 'invalid'}
    if descriptor.get('op_audit_cp_ingest_descriptor_status') != 'described': return {'op_audit_cp_ingest_registration_status': 'invalid'}
    return {'op_audit_cp_ingest_registration_status': 'registered'}
