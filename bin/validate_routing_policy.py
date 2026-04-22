#!/usr/bin/env python3
"""
Validate runtime routing policy and workload profiles for consistency.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_yaml_file(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate_routing_policy_structure(routing_policy):
    """Validate routing policy YAML structure."""
    results = {
        'structure_valid': False,
        'strategies_count': 0,
        'rules_count': 0,
        'issues': []
    }

    required_fields = ['schema_version', 'kind', 'strategies', 'routing_rules']
    missing = [f for f in required_fields if f not in routing_policy]

    if missing:
        results['issues'].append(f"Missing required fields: {missing}")
        return results

    if routing_policy.get('kind') != 'runtime_routing_policy':
        results['issues'].append(f"Invalid kind: {routing_policy.get('kind')}")
        return results

    strategies = routing_policy.get('strategies', [])
    rules = routing_policy.get('routing_rules', [])

    if not strategies:
        results['issues'].append("No strategies defined")
        return results

    if not rules:
        results['issues'].append("No routing rules defined")
        return results

    results['strategies_count'] = len(strategies)
    results['rules_count'] = len(rules)

    # Validate strategies
    strategy_ids = set()
    for strategy in strategies:
        if 'id' not in strategy:
            results['issues'].append("Strategy missing id field")
        else:
            strategy_ids.add(strategy['id'])

    # Validate rules reference existing strategies and profiles
    for rule in rules:
        if 'selected_strategy' not in rule:
            results['issues'].append(f"Rule {rule.get('rule_id')} missing selected_strategy")
        elif rule['selected_strategy'] not in strategy_ids:
            results['issues'].append(f"Rule {rule.get('rule_id')} references unknown strategy: {rule['selected_strategy']}")

    results['structure_valid'] = len(results['issues']) == 0
    return results


def validate_workload_profiles_structure(workload_profiles):
    """Validate workload profiles YAML structure."""
    results = {
        'structure_valid': False,
        'profiles_count': 0,
        'issues': []
    }

    required_fields = ['schema_version', 'kind', 'profiles']
    missing = [f for f in required_fields if f not in workload_profiles]

    if missing:
        results['issues'].append(f"Missing required fields: {missing}")
        return results

    if workload_profiles.get('kind') != 'workload_profiles':
        results['issues'].append(f"Invalid kind: {workload_profiles.get('kind')}")
        return results

    profiles = workload_profiles.get('profiles', [])

    if not profiles:
        results['issues'].append("No profiles defined")
        return results

    results['profiles_count'] = len(profiles)

    # Validate each profile
    profile_ids = set()
    for profile in profiles:
        if 'id' not in profile:
            results['issues'].append("Profile missing id field")
        else:
            profile_ids.add(profile['id'])

        required_profile_fields = [
            'name', 'description', 'max_retry_count', 'validation_intensity',
            'orchestration_mode', 'artifact_expectation_level'
        ]
        missing_profile = [f for f in required_profile_fields if f not in profile]
        if missing_profile:
            results['issues'].append(f"Profile {profile.get('id')} missing fields: {missing_profile}")

    results['structure_valid'] = len(results['issues']) == 0
    return results


def validate_policy_profile_references(routing_policy, workload_profiles):
    """Validate that routing policy rules reference existing profiles."""
    results = {
        'references_valid': False,
        'issues': []
    }

    profile_ids = {p['id'] for p in workload_profiles.get('profiles', [])}
    rules = routing_policy.get('routing_rules', [])

    for rule in rules:
        selected_profile = rule.get('selected_profile')
        if selected_profile and selected_profile not in profile_ids:
            results['issues'].append(f"Rule {rule.get('rule_id')} references unknown profile: {selected_profile}")

    results['references_valid'] = len(results['issues']) == 0
    return results


def main():
    routing_policy_path = Path(__file__).parent.parent / 'governance' / 'runtime_routing_policy.v1.yaml'
    workload_profiles_path = Path(__file__).parent.parent / 'governance' / 'workload_profiles.v1.yaml'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'validation' / 'runtime_routing_validation.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    validation_result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'routing_policy_file': str(routing_policy_path),
        'workload_profiles_file': str(workload_profiles_path),
        'validations': {},
        'overall_status': 'pass',
        'errors': []
    }

    try:
        routing_policy = load_yaml_file(routing_policy_path)
        workload_profiles = load_yaml_file(workload_profiles_path)
    except Exception as e:
        validation_result['overall_status'] = 'fail'
        validation_result['errors'].append(f"Failed to load governance files: {str(e)}")
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"Routing validation FAILED", file=sys.stderr)
        return 1

    # Run validations
    validation_result['validations']['routing_policy_structure'] = validate_routing_policy_structure(routing_policy)
    validation_result['validations']['workload_profiles_structure'] = validate_workload_profiles_structure(workload_profiles)
    validation_result['validations']['policy_profile_references'] = validate_policy_profile_references(routing_policy, workload_profiles)

    # Determine overall status
    if not validation_result['validations']['routing_policy_structure']['structure_valid']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['workload_profiles_structure']['structure_valid']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['policy_profile_references']['references_valid']:
        validation_result['overall_status'] = 'fail'

    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)

    print(f"Routing validation complete: {validation_result['overall_status']}")
    print(f"Output: {output_path}")

    return 0 if validation_result['overall_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
