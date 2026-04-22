#!/usr/bin/env python3
"""
Validate execution run result for consistency, completeness, and routing behavior.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_run_result(path):
    with open(path) as f:
        return json.load(f)


def load_yaml_file(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate_structure(run_result):
    required_fields = [
        'run_id', 'timestamp', 'execution_bundle_path', 'roadmap_ids',
        'dependency_readiness', 'cmdb_resolution', 'routing_decision',
        'orchestration_trace', 'final_state', 'success', 'validations_executed',
        'artifact_outputs', 'ledger_appended'
    ]

    missing = [f for f in required_fields if f not in run_result]
    return {
        'status': 'pass' if not missing else 'fail',
        'missing_fields': missing,
        'total_required': len(required_fields)
    }


def validate_consistency(run_result):
    final_state = run_result.get('final_state')
    success = run_result.get('success')

    results = {
        'final_state': final_state,
        'success_flag': success,
        'consistent': False,
        'issues': []
    }

    if success and final_state != 'succeeded':
        results['issues'].append(f"success=true but final_state={final_state}")

    if not success and final_state == 'succeeded':
        results['issues'].append(f"success=false but final_state={final_state}")

    valid_terminal_states = ['succeeded', 'failed', 'cancelled']
    if final_state not in valid_terminal_states:
        results['issues'].append(f"final_state '{final_state}' not in {valid_terminal_states}")

    results['consistent'] = len(results['issues']) == 0

    return results


def validate_orchestration_trace(run_result):
    trace = run_result.get('orchestration_trace', [])

    results = {
        'total_events': len(trace),
        'valid_events': 0,
        'invalid_events': [],
        'ordering_valid': True,
        'state_sequence': []
    }

    required_trace_fields = ['timestamp', 'from_state', 'event', 'to_state']

    for i, event in enumerate(trace):
        is_valid = True
        errors = []

        for field in required_trace_fields:
            if field not in event:
                is_valid = False
                errors.append(f"missing {field}")

        if is_valid:
            results['valid_events'] += 1
            results['state_sequence'].append({
                'step': i,
                'from': event.get('from_state'),
                'event': event.get('event'),
                'to': event.get('to_state')
            })
        else:
            results['invalid_events'].append({
                'index': i,
                'errors': errors
            })

        if 'timestamp' in event:
            try:
                datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            except:
                results['invalid_events'].append({
                    'index': i,
                    'errors': ['invalid timestamp format']
                })

    if trace and run_result.get('final_state'):
        last_state = trace[-1].get('to_state')
        final_state = run_result.get('final_state')
        if last_state != final_state:
            results['ordering_valid'] = False
            results['invalid_events'].append({
                'issue': f"Final state mismatch: trace ends at {last_state}, run result says {final_state}"
            })

    return results


def validate_dependency_readiness(run_result):
    dep_readiness = run_result.get('dependency_readiness', {})

    results = {
        'has_readiness_data': bool(dep_readiness),
        'checked_items': dep_readiness.get('checked_items', []),
        'all_ready': dep_readiness.get('all_ready'),
        'blocked_items': dep_readiness.get('blocked_items', []),
        'structure_valid': False,
        'issues': []
    }

    required_fields = ['checked_items', 'dependency_status', 'all_ready', 'blocked_items']
    missing = [f for f in required_fields if f not in dep_readiness]

    if missing:
        results['issues'].append(f"missing fields: {missing}")
    else:
        results['structure_valid'] = True

    if dep_readiness.get('all_ready') and dep_readiness.get('blocked_items'):
        results['issues'].append("all_ready=true but blocked_items is non-empty")
        results['structure_valid'] = False

    return results


def validate_cmdb_resolution(run_result):
    cmdb_res = run_result.get('cmdb_resolution', {})

    results = {
        'has_cmdb_data': bool(cmdb_res),
        'subsystems_consulted': cmdb_res.get('subsystems_consulted', []),
        'services_resolved': len(cmdb_res.get('services_resolved', [])),
        'resolution_status': cmdb_res.get('resolution_status'),
        'structure_valid': False,
        'issues': []
    }

    required_fields = ['subsystems_consulted', 'services_resolved', 'resolution_status']
    missing = [f for f in required_fields if f not in cmdb_res]

    if missing:
        results['issues'].append(f"missing fields: {missing}")
    else:
        results['structure_valid'] = True

    valid_statuses = ['success', 'partial', 'failed']
    if cmdb_res.get('resolution_status') not in valid_statuses:
        results['issues'].append(f"invalid resolution_status: {cmdb_res.get('resolution_status')}")
        results['structure_valid'] = False

    return results


def validate_routing_decision(run_result, routing_policy, workload_profiles):
    """Validate routing decision against policy and profiles."""
    routing_decision = run_result.get('routing_decision', {})

    results = {
        'has_routing_data': bool(routing_decision),
        'selected_profile': routing_decision.get('selected_profile'),
        'selected_strategy': routing_decision.get('selected_strategy'),
        'structure_valid': False,
        'profile_valid': False,
        'strategy_valid': False,
        'issues': []
    }

    required_fields = [
        'timestamp', 'selected_profile', 'selected_strategy', 'risk_tier',
        'routing_reasons', 'retry_mode'
    ]
    missing = [f for f in required_fields if f not in routing_decision]

    if missing:
        results['issues'].append(f"missing fields: {missing}")
    else:
        results['structure_valid'] = True

    # Check if profile exists
    if routing_policy and workload_profiles:
        profiles = {p['id']: p for p in workload_profiles.get('profiles', [])}
        if routing_decision.get('selected_profile') in profiles:
            results['profile_valid'] = True
        else:
            results['issues'].append(f"Profile '{routing_decision.get('selected_profile')}' not found in workload_profiles")

        # Check if strategy exists
        strategies = {s['id']: s for s in routing_policy.get('strategies', [])}
        if routing_decision.get('selected_strategy') in strategies:
            results['strategy_valid'] = True
        else:
            results['issues'].append(f"Strategy '{routing_decision.get('selected_strategy')}' not found in routing_policy")

    return results


def validate_retry_summary(run_result):
    """Validate retry summary consistency."""
    retry_summary = run_result.get('retry_summary', {})

    results = {
        'has_retry_data': bool(retry_summary),
        'attempt': retry_summary.get('attempt'),
        'max_attempts': retry_summary.get('max_attempts'),
        'structure_valid': False,
        'issues': []
    }

    required_fields = ['attempt', 'max_attempts', 'retried']
    missing = [f for f in required_fields if f not in retry_summary]

    if missing:
        results['issues'].append(f"missing fields: {missing}")
    else:
        results['structure_valid'] = True

    # Validate that attempt <= max_attempts
    if retry_summary.get('attempt', 0) > retry_summary.get('max_attempts', 1):
        results['issues'].append(f"attempt ({retry_summary.get('attempt')}) > max_attempts ({retry_summary.get('max_attempts')})")
        results['structure_valid'] = False

    return results


def validate_ledger_reference(run_result, ledger_path):
    """Validate that ledger entry exists for this run."""
    results = {
        'ledger_appended': run_result.get('ledger_appended', False),
        'ledger_exists': ledger_path.exists(),
        'run_in_ledger': False,
        'issues': []
    }

    if not results['ledger_exists']:
        results['issues'].append(f"Ledger file not found: {ledger_path}")
        return results

    run_id = run_result.get('run_id')
    try:
        with open(ledger_path, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get('run_id') == run_id:
                    results['run_in_ledger'] = True
                    break
        if not results['run_in_ledger'] and results['ledger_appended']:
            results['issues'].append(f"run_id {run_id} marked as ledger_appended but not found in ledger")
    except Exception as e:
        results['issues'].append(f"Error reading ledger: {str(e)}")

    return results


def validate_artifacts(run_result):
    artifact_outputs = run_result.get('artifact_outputs', [])

    results = {
        'total_artifacts': len(artifact_outputs),
        'valid_artifacts': 0,
        'invalid_artifacts': [],
        'required_artifact_exists': False,
        'all_exist_on_disk': True
    }

    required_fields = ['path', 'type', 'generated']

    for artifact in artifact_outputs:
        is_valid = True
        errors = []

        for field in required_fields:
            if field not in artifact:
                is_valid = False
                errors.append(f"missing {field}")

        if is_valid:
            results['valid_artifacts'] += 1
            if artifact.get('type') == 'run_result':
                results['required_artifact_exists'] = True

            # Check if file exists on disk
            if not Path(artifact.get('path', '')).exists():
                results['all_exist_on_disk'] = False
        else:
            results['invalid_artifacts'].append({
                'errors': errors
            })

    return results


def main():
    run_result_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_result.json'
    routing_policy_path = Path(__file__).parent.parent / 'governance' / 'runtime_routing_policy.v1.yaml'
    workload_profiles_path = Path(__file__).parent.parent / 'governance' / 'workload_profiles.v1.yaml'
    ledger_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_ledger.jsonl'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'validation' / 'execution_run_validation.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    validation_result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'run_result_file': str(run_result_path),
        'validations': {},
        'overall_status': 'pass',
        'errors': []
    }

    try:
        run_result = load_run_result(run_result_path)
    except Exception as e:
        validation_result['overall_status'] = 'fail'
        validation_result['errors'].append(f"Failed to load run result: {str(e)}")
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"Run validation FAILED", file=sys.stderr)
        return 1

    # Load governance files for validation
    routing_policy = None
    workload_profiles = None
    try:
        if routing_policy_path.exists():
            routing_policy = load_yaml_file(routing_policy_path)
        if workload_profiles_path.exists():
            workload_profiles = load_yaml_file(workload_profiles_path)
    except Exception as e:
        validation_result['errors'].append(f"Failed to load governance files: {str(e)}")

    # Run validations
    validation_result['validations']['structure'] = validate_structure(run_result)
    validation_result['validations']['consistency'] = validate_consistency(run_result)
    validation_result['validations']['orchestration_trace'] = validate_orchestration_trace(run_result)
    validation_result['validations']['dependency_readiness'] = validate_dependency_readiness(run_result)
    validation_result['validations']['cmdb_resolution'] = validate_cmdb_resolution(run_result)
    validation_result['validations']['routing_decision'] = validate_routing_decision(run_result, routing_policy, workload_profiles)
    validation_result['validations']['retry_summary'] = validate_retry_summary(run_result)
    validation_result['validations']['ledger'] = validate_ledger_reference(run_result, ledger_path)
    validation_result['validations']['artifacts'] = validate_artifacts(run_result)

    # Determine overall status
    if validation_result['validations']['structure']['status'] == 'fail':
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['consistency']['consistent']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['orchestration_trace']['ordering_valid']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['dependency_readiness']['structure_valid']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['cmdb_resolution']['structure_valid']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['routing_decision']['structure_valid']:
        validation_result['overall_status'] = 'fail'
    if not validation_result['validations']['retry_summary']['structure_valid']:
        validation_result['overall_status'] = 'fail'
    if validation_result['validations']['artifacts']['invalid_artifacts']:
        validation_result['overall_status'] = 'fail'

    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)

    print(f"Run validation complete: {validation_result['overall_status']}")
    print(f"Output: {output_path}")

    return 0 if validation_result['overall_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
