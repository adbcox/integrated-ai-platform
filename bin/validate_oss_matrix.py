#!/usr/bin/env python3
"""
Validate OSS capability matrix for consistency and completeness.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_matrix(matrix_path):
    """Load OSS capability matrix."""
    with open(matrix_path) as f:
        return yaml.safe_load(f)


def validate_candidates(matrix):
    """Validate each candidate entry."""
    candidates = matrix.get('candidates', [])
    results = {
        'total': len(candidates),
        'valid': 0,
        'invalid': [],
        'decision_distribution': {}
    }

    required_fields = ['name', 'category', 'license', 'integration_fit', 'decision']
    valid_decisions = ['adopt', 'evaluate', 'reject', 'watch']
    valid_fit = ['high', 'medium', 'low']

    for candidate in candidates:
        is_valid = True
        errors = []

        # Check required fields
        for field in required_fields:
            if field not in candidate:
                is_valid = False
                errors.append(f"missing {field}")

        # Check decision is valid
        decision = candidate.get('decision')
        if decision not in valid_decisions:
            is_valid = False
            errors.append(f"invalid decision: {decision}")
        else:
            results['decision_distribution'][decision] = results['decision_distribution'].get(decision, 0) + 1

        # Check integration_fit is valid
        fit = candidate.get('integration_fit')
        if fit not in valid_fit:
            is_valid = False
            errors.append(f"invalid integration_fit: {fit}")

        if is_valid:
            results['valid'] += 1
        else:
            results['invalid'].append({
                'name': candidate.get('name'),
                'errors': errors
            })

    return results


def validate_decision_consistency(matrix):
    """Validate that decision_summary matches candidate decisions."""
    candidates = matrix.get('candidates', [])
    decision_summary = matrix.get('decision_summary', {})

    results = {
        'summary_keys_valid': False,
        'mismatches': []
    }

    # Verify decision_summary has required keys
    required_keys = ['adopt', 'evaluate', 'watch', 'reject']
    summary_keys = set(decision_summary.keys())
    results['summary_keys_valid'] = all(k in summary_keys for k in required_keys)

    # Build actual decision map
    actual_decisions = {
        'adopt': [],
        'evaluate': [],
        'watch': [],
        'reject': []
    }

    for candidate in candidates:
        decision = candidate.get('decision')
        if decision in actual_decisions:
            actual_decisions[decision].append(candidate['name'])

    # Compare
    for decision_type, expected_items in decision_summary.items():
        actual_items = actual_decisions.get(decision_type, [])
        expected_set = set(expected_items) if expected_items else set()
        actual_set = set(actual_items)

        if expected_set != actual_set:
            results['mismatches'].append({
                'decision': decision_type,
                'missing_from_summary': list(actual_set - expected_set),
                'extra_in_summary': list(expected_set - actual_set)
            })

    return results


def validate_integration_links(matrix):
    """Validate that candidates link to valid subsystems."""
    candidates = matrix.get('candidates', [])
    valid_subsystems = [
        'control_plane', 'runtime', 'inference', 'retrieval', 'evaluation'
    ]

    results = {
        'linked': 0,
        'unlinked': [],
        'invalid_subsystem': []
    }

    for candidate in candidates:
        linked_subsystem = candidate.get('linked_subsystem')
        if not linked_subsystem:
            results['unlinked'].append(candidate.get('name'))
        elif linked_subsystem not in valid_subsystems:
            results['invalid_subsystem'].append({
                'candidate': candidate.get('name'),
                'subsystem': linked_subsystem
            })
        else:
            results['linked'] += 1

    return results


def validate_adoption_levels(matrix):
    """Validate decision_summary and integration_verification alignment."""
    results = {
        'integration_verification_items': 0,
        'status_distribution': {},
        'mismatch_with_candidates': []
    }

    integration_verification = matrix.get('integration_verification', [])
    candidates = matrix.get('candidates', [])
    candidate_names = {c['name'] for c in candidates}

    for item in integration_verification:
        results['integration_verification_items'] += 1
        status = item.get('status')
        results['status_distribution'][status] = results['status_distribution'].get(status, 0) + 1

        # Check that referenced tools exist
        tools = item.get('tools', [])
        for tool in tools:
            if tool not in candidate_names:
                results['mismatch_with_candidates'].append({
                    'subsystem': item.get('subsystem'),
                    'tool': tool,
                    'reason': 'tool not found in candidates'
                })

    return results


def main():
    """Validate OSS capability matrix."""
    matrix_path = Path(__file__).parent.parent / 'governance' / 'oss_capability_matrix.v1.yaml'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'validation' / 'oss_matrix_validation.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    validation_result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'matrix_file': str(matrix_path),
        'validations': {},
        'overall_status': 'pass',
        'errors': []
    }

    try:
        matrix = load_matrix(matrix_path)
    except Exception as e:
        validation_result['overall_status'] = 'fail'
        validation_result['errors'].append(f"Failed to load matrix: {str(e)}")
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"OSS matrix validation FAILED", file=sys.stderr)
        return 1

    # Run validations
    validation_result['validations']['candidates'] = validate_candidates(matrix)
    validation_result['validations']['decision_consistency'] = validate_decision_consistency(matrix)
    validation_result['validations']['integration_links'] = validate_integration_links(matrix)
    validation_result['validations']['adoption_levels'] = validate_adoption_levels(matrix)

    # Determine overall status
    if validation_result['validations']['candidates']['invalid']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['decision_consistency']['mismatches']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['integration_links']['invalid_subsystem']:
        validation_result['overall_status'] = 'fail'

    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)

    print(f"OSS matrix validation complete: {validation_result['overall_status']}")
    print(f"Total candidates: {validation_result['validations']['candidates']['total']}")
    print(f"Valid: {validation_result['validations']['candidates']['valid']}")
    print(f"Output: {output_path}")

    return 0 if validation_result['overall_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
