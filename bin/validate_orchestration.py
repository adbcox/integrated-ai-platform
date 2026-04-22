#!/usr/bin/env python3
"""
Validate orchestration model for consistency and completeness.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_orchestration(orch_path):
    """Load orchestration model."""
    with open(orch_path) as f:
        return yaml.safe_load(f)


def validate_event_types(model):
    """Validate event type definitions."""
    event_types = model.get('event_types', [])
    results = {
        'total': len(event_types),
        'valid': 0,
        'invalid': [],
        'handlers': set()
    }

    required_fields = ['id', 'name', 'description']

    for event_type in event_types:
        is_valid = True
        errors = []

        for field in required_fields:
            if field not in event_type:
                is_valid = False
                errors.append(f"missing {field}")

        if event_type.get('handler'):
            results['handlers'].add(event_type['handler'])

        if is_valid:
            results['valid'] += 1
        else:
            results['invalid'].append({
                'event_id': event_type.get('id'),
                'errors': errors
            })

    results['handlers'] = list(results['handlers'])
    return results


def validate_job_states(model):
    """Validate job state definitions."""
    job_states = model.get('job_states', [])
    results = {
        'total': len(job_states),
        'valid': 0,
        'invalid': [],
        'state_ids': []
    }

    required_fields = ['id', 'name', 'description', 'valid_transitions']

    for state in job_states:
        is_valid = True
        errors = []

        for field in required_fields:
            if field not in state:
                is_valid = False
                errors.append(f"missing {field}")

        state_id = state.get('id')
        results['state_ids'].append(state_id)

        if is_valid:
            results['valid'] += 1
        else:
            results['invalid'].append({
                'state_id': state_id,
                'errors': errors
            })

    return results


def validate_state_transitions(model):
    """Validate state transition definitions."""
    transitions = model.get('state_transitions', [])
    state_ids = set(s['id'] for s in model.get('job_states', []))

    results = {
        'total': len(transitions),
        'valid': 0,
        'invalid': [],
        'invalid_references': []
    }

    for transition in transitions:
        is_valid = True
        errors = []

        # Check required fields
        for field in ['from', 'to', 'event']:
            if field not in transition:
                is_valid = False
                errors.append(f"missing {field}")

        # Check from/to reference valid states
        from_state = transition.get('from')
        to_state = transition.get('to')

        if from_state and from_state not in state_ids:
            is_valid = False
            errors.append(f"from state '{from_state}' not defined")
            results['invalid_references'].append({
                'transition': f"{from_state} -> {to_state}",
                'issue': f"from state not defined"
            })

        if to_state and to_state not in state_ids:
            is_valid = False
            errors.append(f"to state '{to_state}' not defined")
            results['invalid_references'].append({
                'transition': f"{from_state} -> {to_state}",
                'issue': f"to state not defined"
            })

        if is_valid:
            results['valid'] += 1
        else:
            results['invalid'].append({
                'transition': f"{from_state} -> {to_state}",
                'errors': errors
            })

    return results


def validate_transition_graph(model):
    """Validate that job state transitions form a valid DAG."""
    transitions = model.get('state_transitions', [])
    job_states = model.get('job_states', [])

    # Check that declared valid_transitions in states match state_transitions
    results = {
        'state_transitions_consistency': True,
        'mismatches': []
    }

    state_dict = {s['id']: s for s in job_states}

    for state_id, state_data in state_dict.items():
        declared_transitions = set()
        for vt in state_data.get('valid_transitions', []):
            declared_transitions.add((state_id, vt.get('to')))

        actual_transitions = set()
        for trans in transitions:
            if trans.get('from') == state_id:
                actual_transitions.add((state_id, trans.get('to')))

        if declared_transitions != actual_transitions:
            results['state_transitions_consistency'] = False
            results['mismatches'].append({
                'state': state_id,
                'in_valid_transitions_not_in_transitions': list(declared_transitions - actual_transitions),
                'in_transitions_not_in_valid_transitions': list(actual_transitions - declared_transitions)
            })

    return results


def validate_retry_policy(model):
    """Validate retry policy configuration."""
    retry_policy = model.get('retry_policy', {})
    results = {
        'has_policy': bool(retry_policy),
        'fields_present': [],
        'issues': []
    }

    required_fields = ['max_retries', 'retry_delay_seconds', 'backoff_multiplier']

    for field in required_fields:
        if field in retry_policy:
            results['fields_present'].append(field)
        else:
            results['issues'].append(f"missing {field}")

    if retry_policy.get('max_retries', 0) < 0:
        results['issues'].append("max_retries cannot be negative")

    if retry_policy.get('backoff_multiplier', 1.0) <= 0:
        results['issues'].append("backoff_multiplier must be positive")

    return results


def validate_failure_policy(model):
    """Validate failure policy configuration."""
    failure_policy = model.get('failure_policy', {})
    results = {
        'has_policy': bool(failure_policy),
        'policies_defined': list(failure_policy.keys()),
        'issues': []
    }

    # Should have at least some failure handlers
    if not failure_policy:
        results['issues'].append("failure_policy is empty")

    return results


def main():
    """Validate orchestration model."""
    orch_path = Path(__file__).parent.parent / 'governance' / 'orchestration_model.v1.yaml'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'validation' / 'orchestration_validation.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    validation_result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'orchestration_file': str(orch_path),
        'validations': {},
        'overall_status': 'pass',
        'errors': []
    }

    try:
        model = load_orchestration(orch_path)
    except Exception as e:
        validation_result['overall_status'] = 'fail'
        validation_result['errors'].append(f"Failed to load orchestration model: {str(e)}")
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"Orchestration validation FAILED", file=sys.stderr)
        return 1

    # Run validations
    validation_result['validations']['event_types'] = validate_event_types(model)
    validation_result['validations']['job_states'] = validate_job_states(model)
    validation_result['validations']['state_transitions'] = validate_state_transitions(model)
    validation_result['validations']['transition_graph'] = validate_transition_graph(model)
    validation_result['validations']['retry_policy'] = validate_retry_policy(model)
    validation_result['validations']['failure_policy'] = validate_failure_policy(model)

    # Determine overall status
    if validation_result['validations']['event_types']['invalid']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['job_states']['invalid']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['state_transitions']['invalid_references']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['transition_graph']['state_transitions_consistency']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['retry_policy']['issues']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['failure_policy']['issues']:
        validation_result['overall_status'] = 'fail'

    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)

    print(f"Orchestration validation complete: {validation_result['overall_status']}")
    print(f"Event types: {validation_result['validations']['event_types']['total']}")
    print(f"Job states: {validation_result['validations']['job_states']['total']}")
    print(f"State transitions: {validation_result['validations']['state_transitions']['total']}")
    print(f"Output: {output_path}")

    return 0 if validation_result['overall_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
