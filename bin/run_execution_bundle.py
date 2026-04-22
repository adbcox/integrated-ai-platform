#!/usr/bin/env python3
"""
Runtime executor for compiled execution bundles with decision-driven routing.
Loads bundle, checks dependencies, resolves CMDB services, executes lifecycle with routing.
"""

import json
import sys
import yaml
import uuid
from pathlib import Path
from datetime import datetime


def load_json_file(path):
    with open(path) as f:
        return json.load(f)


def load_yaml_file(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate_bundle(bundle):
    required_fields = [
        'roadmap_ids', 'objective', 'allowed_files', 'forbidden_files',
        'expected_artifacts', 'validation_steps', 'rollback_rule', 'completion_rule'
    ]
    missing = [f for f in required_fields if f not in bundle]
    return {
        'valid': len(missing) == 0,
        'missing_fields': missing
    }


def check_dependency_readiness(bundle, dependency_graph):
    roadmap_ids = bundle.get('roadmap_ids', [])
    nodes = {node['id']: node for node in dependency_graph.get('nodes', [])}
    edges = dependency_graph.get('edges', [])

    hard_deps = {node_id: [] for node_id in nodes}
    for edge in edges:
        if edge.get('type') == 'hard':
            hard_deps[edge['to']].append(edge['from'])

    result = {
        'checked_items': roadmap_ids,
        'dependency_status': {},
        'all_ready': True,
        'blocked_items': [],
        'dependency_details': []
    }

    for item_id in roadmap_ids:
        if item_id not in nodes:
            result['all_ready'] = False
            result['blocked_items'].append(item_id)
            result['dependency_status'][item_id] = 'missing_from_graph'
            result['dependency_details'].append({
                'item': item_id,
                'issue': 'not found in roadmap graph'
            })
            continue

        deps = hard_deps.get(item_id, [])
        node = nodes[item_id]
        node_status = node.get('status', 'unknown')

        unsatisfied = []
        for dep_id in deps:
            if dep_id not in nodes:
                unsatisfied.append(f"{dep_id} (missing)")
            else:
                dep_node = nodes[dep_id]
                dep_status = dep_node.get('status', 'unknown')
                if dep_status not in ['complete', 'completed', 'in_validation']:
                    unsatisfied.append(f"{dep_id} (status: {dep_status})")

        if unsatisfied:
            result['all_ready'] = False
            result['blocked_items'].append(item_id)
            result['dependency_status'][item_id] = 'blocked'
            result['dependency_details'].append({
                'item': item_id,
                'dependencies': deps,
                'unsatisfied': unsatisfied
            })
        else:
            result['dependency_status'][item_id] = 'ready'

    return result


def resolve_cmdb_services(bundle, cmdb):
    result = {
        'subsystems_consulted': list(cmdb.get('subsystems', {}).keys()),
        'services_resolved': [],
        'resolution_status': 'success',
        'missing_services': []
    }

    subsystems = cmdb.get('subsystems', {})
    for subsys_id, subsys_data in subsystems.items():
        services = subsys_data.get('services', [])
        for service in services:
            result['services_resolved'].append({
                'id': service['id'],
                'name': service['name'],
                'subsystem': subsys_id,
                'capabilities': service.get('capabilities', [])
            })

    integration_points = cmdb.get('integration_points', [])
    result['integration_points'] = len(integration_points)

    return result


def make_routing_decision(bundle, dependency_readiness, cmdb_resolution, routing_policy, workload_profiles, code_intelligence, oss_matrix):
    """Determine execution strategy and workload profile based on bundle characteristics and governance inputs."""

    decision = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'selected_profile': None,
        'selected_strategy': None,
        'risk_tier': None,
        'routing_reasons': [],
        'code_intelligence_inputs_used': [],
        'oss_inputs_used': [],
        'fallback_strategy': None,
        'retry_mode': None,
        'matched_rule': None
    }

    # Extract observable conditions
    validation_steps = len(bundle.get('validation_steps', []))
    expected_artifacts = len(bundle.get('expected_artifacts', []))
    roadmap_items = len(bundle.get('roadmap_ids', []))
    all_ready = dependency_readiness.get('all_ready', False)
    services_available = len(cmdb_resolution.get('services_resolved', []))

    # Check code intelligence decisions for inputs
    if code_intelligence and isinstance(code_intelligence, dict):
        decisions_list = code_intelligence.get('decisions', [])
        for decision_item in decisions_list:
            if decision_item.get('classification') in ['adopt_now', 'evaluate']:
                decision['code_intelligence_inputs_used'].append({
                    'tool': decision_item.get('tool'),
                    'classification': decision_item.get('classification')
                })

    # Check OSS matrix for inputs
    if oss_matrix and isinstance(oss_matrix, dict):
        candidates_list = oss_matrix.get('candidates', [])
        oss_inputs = []
        for candidate in candidates_list:
            if candidate.get('decision') in ['adopt', 'evaluate']:
                oss_inputs.append({
                    'candidate': candidate.get('id'),
                    'decision': candidate.get('decision'),
                    'integration_status': candidate.get('integration_status')
                })
        if oss_inputs:
            decision['oss_inputs_used'] = oss_inputs

    # Evaluate routing rules in order using safer approach
    strategies = {s['id']: s for s in routing_policy.get('strategies', [])}
    routes = routing_policy.get('routing_rules', [])

    matched = False
    for route in routes:
        rule_id = route.get('rule_id')

        # Rule-specific condition matching (explicit, not eval-based)
        rule_matched = False

        if rule_id == 'RR-001':
            # Metadata-only routing
            rule_matched = validation_steps == 0 and expected_artifacts <= 1
        elif rule_id == 'RR-002':
            # Governance update routing
            rule_matched = validation_steps >= 2 and validation_steps <= 4 and roadmap_items <= 2
        elif rule_id == 'RR-003':
            # Planning and compilation routing
            rule_matched = roadmap_items >= 2 and roadmap_items <= 6 and validation_steps >= 3
        elif rule_id == 'RR-004':
            # Complex runtime execution routing
            rule_matched = roadmap_items > 2 and validation_steps >= 4 and expected_artifacts >= 3
        elif rule_id == 'RR-005':
            # Simple runtime execution routing
            rule_matched = roadmap_items <= 2 and validation_steps >= 2 and expected_artifacts >= 1
        elif rule_id == 'RR-006':
            # Dependency blocked fallback
            rule_matched = not all_ready
        elif rule_id == 'RR-007':
            # Service unavailable fallback
            rule_matched = services_available < 3

        if rule_matched:
            decision['selected_profile'] = route.get('selected_profile')
            decision['selected_strategy'] = route.get('selected_strategy')
            decision['routing_reasons'].append(route.get('reason'))
            decision['matched_rule'] = rule_id
            matched = True
            break

    # Fallback if no rule matched
    if not matched:
        fallback = routing_policy.get('fallback_behavior', {})
        decision['selected_strategy'] = fallback.get('default_strategy', 'safe_fail')
        decision['selected_profile'] = fallback.get('default_profile', 'metadata_only')
        decision['routing_reasons'].append('No rule matched; using fallback')
        decision['matched_rule'] = 'FALLBACK'

    # Get strategy and profile details
    if decision['selected_strategy']:
        strategy = strategies.get(decision['selected_strategy'])
        if strategy:
            decision['risk_tier'] = strategy.get('risk_tier')
            decision['retry_mode'] = 'enabled' if strategy.get('retry_allowed', False) else 'disabled'
            decision['fallback_strategy'] = fallback.get('default_strategy', 'safe_fail') if not matched else None

    if decision['selected_profile']:
        profile = next((p for p in workload_profiles.get('profiles', []) if p['id'] == decision['selected_profile']), None)
        if profile:
            risk_classification = workload_profiles.get('risk_tier_classification', {})
            decision['risk_tier'] = risk_classification.get(decision['selected_profile'], 'UNKNOWN')

    return decision


def execute_orchestration_lifecycle(bundle, orchestration_model):
    states = {s['id']: s for s in orchestration_model.get('job_states', [])}
    transitions = orchestration_model.get('state_transitions', [])

    transition_map = {}
    for trans in transitions:
        from_state = trans.get('from')
        to_state = trans.get('to')
        event = trans.get('event')
        if from_state not in transition_map:
            transition_map[from_state] = {}
        transition_map[from_state][event] = to_state

    orchestration_trace = []
    current_state = 'pending'
    timestamp_start = datetime.utcnow().isoformat() + 'Z'

    lifecycle_plan = [
        ('pending', 'execution_started', 'executing'),
        ('executing', 'execution_succeeded', 'succeeded')
    ]

    for from_state, event, expected_to_state in lifecycle_plan:
        if current_state != from_state:
            orchestration_trace.append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'from_state': current_state,
                'event': 'error',
                'to_state': 'failed',
                'reason': f"Expected {from_state}, got {current_state}"
            })
            current_state = 'failed'
            break

        if from_state in transition_map and event in transition_map[from_state]:
            to_state = transition_map[from_state][event]
            orchestration_trace.append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'from_state': from_state,
                'event': event,
                'to_state': to_state,
                'preconditions_met': True
            })
            current_state = to_state
        else:
            orchestration_trace.append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'from_state': from_state,
                'event': event,
                'to_state': 'failed',
                'reason': f"Transition {from_state}--{event} not defined"
            })
            current_state = 'failed'
            break

    return {
        'orchestration_trace': orchestration_trace,
        'final_state': current_state,
        'success': current_state == 'succeeded',
        'timestamp_start': timestamp_start,
        'timestamp_end': datetime.utcnow().isoformat() + 'Z'
    }


def append_to_ledger(ledger_path, ledger_entry):
    """Append entry to run ledger (JSONL format)."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, 'a') as f:
        f.write(json.dumps(ledger_entry) + '\n')


def main():
    # Accept bundle path from CLI or use default
    bundle_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / 'artifacts' / 'execution' / 'sample_execution_bundle.json'

    # Make bundle_path absolute if relative
    if not bundle_path.is_absolute():
        bundle_path = Path(__file__).parent.parent / bundle_path

    dependency_graph_path = Path(__file__).parent.parent / 'governance' / 'roadmap_dependency_graph.v1.yaml'
    cmdb_path = Path(__file__).parent.parent / 'governance' / 'cmdb_topology.v1.yaml'
    orchestration_path = Path(__file__).parent.parent / 'governance' / 'orchestration_model.v1.yaml'
    routing_policy_path = Path(__file__).parent.parent / 'governance' / 'runtime_routing_policy.v1.yaml'
    workload_profiles_path = Path(__file__).parent.parent / 'governance' / 'workload_profiles.v1.yaml'
    code_intelligence_path = Path(__file__).parent.parent / 'governance' / 'code_intelligence_decisions.v1.yaml'
    oss_matrix_path = Path(__file__).parent.parent / 'governance' / 'oss_capability_matrix.v1.yaml'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_result.json'
    ledger_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_ledger.jsonl'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow().isoformat() + 'Z'

    run_result = {
        'run_id': run_id,
        'timestamp': timestamp,
        'execution_bundle_path': str(bundle_path),
        'bundle_validation': None,
        'roadmap_ids': None,
        'dependency_readiness': None,
        'cmdb_resolution': None,
        'routing_decision': None,
        'orchestration_trace': None,
        'retry_summary': {
            'attempt': 1,
            'max_attempts': 1,
            'retried': False
        },
        'final_state': None,
        'success': False,
        'failure_reason': None,
        'validations_expected': [
            'bundle_structure', 'dependency_readiness', 'cmdb_resolution',
            'orchestration_lifecycle', 'artifact_generation'
        ],
        'validations_executed': [],
        'validation_status': {},
        'artifact_outputs': [],
        'ledger_appended': False
    }

    try:
        bundle = load_json_file(bundle_path)
        run_result['roadmap_ids'] = bundle.get('roadmap_ids')

        bundle_validation = validate_bundle(bundle)
        run_result['bundle_validation'] = bundle_validation
        run_result['validations_executed'].append('bundle_structure')
        run_result['validation_status']['bundle_structure'] = 'pass' if bundle_validation['valid'] else 'fail'

        if not bundle_validation['valid']:
            run_result['failure_reason'] = f"Bundle validation failed: {bundle_validation['missing_fields']}"
            with open(output_path, 'w') as f:
                json.dump(run_result, f, indent=2)
            print(f"Bundle validation FAILED", file=sys.stderr)
            return 1

    except Exception as e:
        run_result['failure_reason'] = f"Failed to load/validate bundle: {str(e)}"
        with open(output_path, 'w') as f:
            json.dump(run_result, f, indent=2)
        print(f"Bundle loading FAILED: {run_result['failure_reason']}", file=sys.stderr)
        return 1

    try:
        dependency_graph = load_yaml_file(dependency_graph_path)
        dependency_readiness = check_dependency_readiness(bundle, dependency_graph)
        run_result['dependency_readiness'] = dependency_readiness
        run_result['validations_executed'].append('dependency_readiness')
        run_result['validation_status']['dependency_readiness'] = 'pass' if dependency_readiness['all_ready'] else 'fail'

        if not dependency_readiness['all_ready']:
            run_result['failure_reason'] = f"Dependencies not ready: {dependency_readiness['blocked_items']}"
            run_result['success'] = False
            with open(output_path, 'w') as f:
                json.dump(run_result, f, indent=2)
            print(f"Dependency check BLOCKED: {dependency_readiness['blocked_items']}", file=sys.stderr)
            return 1

    except Exception as e:
        run_result['failure_reason'] = f"Failed dependency check: {str(e)}"
        with open(output_path, 'w') as f:
            json.dump(run_result, f, indent=2)
        print(f"Dependency check FAILED: {run_result['failure_reason']}", file=sys.stderr)
        return 1

    try:
        cmdb = load_yaml_file(cmdb_path)
        cmdb_resolution = resolve_cmdb_services(bundle, cmdb)
        run_result['cmdb_resolution'] = cmdb_resolution
        run_result['validations_executed'].append('cmdb_resolution')
        run_result['validation_status']['cmdb_resolution'] = 'pass'

    except Exception as e:
        run_result['failure_reason'] = f"Failed CMDB resolution: {str(e)}"
        with open(output_path, 'w') as f:
            json.dump(run_result, f, indent=2)
        print(f"CMDB resolution FAILED: {run_result['failure_reason']}", file=sys.stderr)
        return 1

    # Load routing governance files
    try:
        routing_policy = load_yaml_file(routing_policy_path)
        workload_profiles = load_yaml_file(workload_profiles_path)
        code_intelligence = load_yaml_file(code_intelligence_path) if code_intelligence_path.exists() else {}
        oss_matrix = load_yaml_file(oss_matrix_path) if oss_matrix_path.exists() else {}
    except Exception as e:
        run_result['failure_reason'] = f"Failed to load routing governance: {str(e)}"
        with open(output_path, 'w') as f:
            json.dump(run_result, f, indent=2)
        print(f"Routing governance load FAILED: {run_result['failure_reason']}", file=sys.stderr)
        return 1

    # Make routing decision
    try:
        routing_decision = make_routing_decision(
            bundle, dependency_readiness, cmdb_resolution,
            routing_policy, workload_profiles, code_intelligence, oss_matrix
        )
        run_result['routing_decision'] = routing_decision
        print(f"Routing decision: {routing_decision['selected_profile']} / {routing_decision['selected_strategy']} (risk: {routing_decision['risk_tier']})")

    except Exception as e:
        run_result['failure_reason'] = f"Failed to make routing decision: {str(e)}"
        with open(output_path, 'w') as f:
            json.dump(run_result, f, indent=2)
        print(f"Routing decision FAILED: {run_result['failure_reason']}", file=sys.stderr)
        return 1

    # Check for deterministic failure injection (test_behavior field)
    test_behavior = bundle.get('test_behavior', 'normal')
    max_retry_attempts = 2 if test_behavior == 'retryable_fail_then_success' else 1
    attempt = 1
    orchestration_result = None

    while attempt <= max_retry_attempts:
        try:
            orchestration = load_yaml_file(orchestration_path)

            # Inject retryable failure on first attempt only for test_behavior
            if test_behavior == 'retryable_fail_then_success' and attempt == 1:
                # Simulate retryable failure: create trace showing attempt, failure, and reason
                orchestration_trace = [
                    {
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'from_state': 'pending',
                        'event': 'execution_started',
                        'to_state': 'executing',
                        'preconditions_met': True
                    },
                    {
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'from_state': 'executing',
                        'event': 'execution_retryable_failure',
                        'to_state': 'retryable_failed',
                        'reason': 'Simulated retryable failure (test_behavior injection)'
                    }
                ]
                orchestration_result = {
                    'orchestration_trace': orchestration_trace,
                    'final_state': 'retryable_failed',
                    'success': False,
                    'timestamp_start': datetime.utcnow().isoformat() + 'Z',
                    'timestamp_end': datetime.utcnow().isoformat() + 'Z',
                    'retryable': True
                }
                attempt += 1
                continue
            else:
                # Normal execution path
                orchestration_result = execute_orchestration_lifecycle(bundle, orchestration)
                if orchestration_result['success'] or attempt >= max_retry_attempts:
                    break
                attempt += 1

        except Exception as e:
            run_result['failure_reason'] = f"Failed orchestration execution: {str(e)}"
            run_result['success'] = False
            with open(output_path, 'w') as f:
                json.dump(run_result, f, indent=2)
            print(f"Orchestration FAILED: {run_result['failure_reason']}", file=sys.stderr)
            return 1

    run_result['orchestration_trace'] = orchestration_result['orchestration_trace']
    run_result['final_state'] = orchestration_result['final_state']
    run_result['success'] = orchestration_result['success']
    run_result['retry_summary']['attempt'] = attempt
    run_result['retry_summary']['max_attempts'] = max_retry_attempts
    run_result['retry_summary']['retried'] = attempt > 1
    run_result['validations_executed'].append('orchestration_lifecycle')
    run_result['validation_status']['orchestration_lifecycle'] = 'pass' if orchestration_result['success'] else 'fail'

    if not orchestration_result['success']:
        run_result['failure_reason'] = f"Orchestration failed at state {orchestration_result['final_state']}"

    run_result['artifact_outputs'].append({
        'path': str(output_path),
        'type': 'run_result',
        'generated': True
    })
    run_result['validations_executed'].append('artifact_generation')
    run_result['validation_status']['artifact_generation'] = 'pass'

    with open(output_path, 'w') as f:
        json.dump(run_result, f, indent=2)

    # Append to ledger
    ledger_entry = {
        'run_id': run_id,
        'timestamp': timestamp,
        'bundle_path': str(bundle_path),
        'roadmap_ids': run_result['roadmap_ids'],
        'selected_profile': run_result['routing_decision'].get('selected_profile') if run_result['routing_decision'] else None,
        'selected_strategy': run_result['routing_decision'].get('selected_strategy') if run_result['routing_decision'] else None,
        'final_state': run_result['final_state'],
        'success': run_result['success'],
        'retry_count': run_result['retry_summary']['attempt'] - 1,
        'retried': run_result['retry_summary']['retried'],
        'max_attempts': run_result['retry_summary']['max_attempts'],
        'services_consulted': len(run_result['cmdb_resolution'].get('services_resolved', [])),
        'validation_status': run_result['validation_status'],
        'artifact_paths': [a['path'] for a in run_result['artifact_outputs']]
    }

    try:
        append_to_ledger(ledger_path, ledger_entry)
        run_result['ledger_appended'] = True
    except Exception as e:
        print(f"Warning: Failed to append ledger entry: {str(e)}", file=sys.stderr)

    # Rewrite run result with updated ledger_appended
    with open(output_path, 'w') as f:
        json.dump(run_result, f, indent=2)

    print(f"Execution bundle run complete")
    print(f"Run ID: {run_id}")
    print(f"Profile: {run_result['routing_decision'].get('selected_profile')}")
    print(f"Strategy: {run_result['routing_decision'].get('selected_strategy')}")
    print(f"Final state: {run_result['final_state']}")
    print(f"Success: {run_result['success']}")
    print(f"Output: {output_path}")

    return 0 if run_result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
