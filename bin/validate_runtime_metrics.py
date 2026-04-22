#!/usr/bin/env python3
"""
Validate runtime metrics for consistency and correctness.
Checks that metrics are properly computed and internally consistent.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def validate_metrics(metrics, ledger_path):
    """Validate runtime metrics for correctness."""
    validation_result = {
        'metrics_valid': True,
        'required_fields': [],
        'issues': [],
        'consistency_checks': {}
    }

    # Check required fields
    required_fields = [
        'ledger_entry_count', 'total_runs', 'successful_runs', 'failed_runs',
        'retried_runs', 'first_pass_success_count', 'first_pass_success_rate',
        'average_retry_count', 'runs_by_profile', 'runs_by_strategy', 'runs_by_final_state',
        'most_recent_run_id', 'most_recent_timestamp'
    ]

    for field in required_fields:
        if field not in metrics:
            validation_result['issues'].append(f"Missing required field: {field}")
            validation_result['metrics_valid'] = False
        else:
            validation_result['required_fields'].append(field)

    # Consistency check: total_runs should equal successful + failed
    total_computed = metrics.get('successful_runs', 0) + metrics.get('failed_runs', 0)
    total_runs = metrics.get('total_runs', 0)
    if total_computed != total_runs:
        validation_result['issues'].append(
            f"Run count mismatch: successful ({metrics['successful_runs']}) + failed ({metrics['failed_runs']}) = {total_computed}, but total_runs = {total_runs}"
        )
        validation_result['metrics_valid'] = False
    validation_result['consistency_checks']['run_count_sum'] = total_computed == total_runs

    # Consistency check: retry_success_count <= retried_runs
    retry_success = metrics.get('retry_success_count', 0)
    retried_runs = metrics.get('retried_runs', 0)
    if retry_success > retried_runs:
        validation_result['issues'].append(
            f"Retry success count ({retry_success}) exceeds retried_runs ({retried_runs})"
        )
        validation_result['metrics_valid'] = False
    validation_result['consistency_checks']['retry_count_valid'] = retry_success <= retried_runs

    # Consistency check: first_pass_success_count + retry_success_count <= total_successful
    first_pass = metrics.get('first_pass_success_count', 0)
    total_successful = metrics.get('successful_runs', 0)
    if first_pass + retry_success > total_successful:
        validation_result['issues'].append(
            f"First-pass ({first_pass}) + retry success ({retry_success}) exceeds total successful ({total_successful})"
        )
        validation_result['metrics_valid'] = False
    validation_result['consistency_checks']['success_accounting_valid'] = (first_pass + retry_success) <= total_successful

    # Consistency check: rates are in valid range [0, 1]
    for rate_name in ['first_pass_success_rate', 'retry_success_rate', 'artifact_generation_rate']:
        rate = metrics.get(rate_name, 0)
        if not (0.0 <= rate <= 1.0):
            validation_result['issues'].append(f"{rate_name} out of range [0, 1]: {rate}")
            validation_result['metrics_valid'] = False
        validation_result['consistency_checks'][f'{rate_name}_in_range'] = (0.0 <= rate <= 1.0)

    # Consistency check: validation pass rates are in range
    validation_rates = metrics.get('validation_pass_rate', {})
    for val_type, rate in validation_rates.items():
        if not (0.0 <= rate <= 1.0):
            validation_result['issues'].append(f"Validation pass rate for {val_type} out of range: {rate}")
            validation_result['metrics_valid'] = False

    # Check that profile/strategy/state breakdowns are dicts
    for key in ['runs_by_profile', 'runs_by_strategy', 'runs_by_final_state']:
        if not isinstance(metrics.get(key), dict):
            validation_result['issues'].append(f"{key} is not a dict")
            validation_result['metrics_valid'] = False

    # If most_recent_run_id and most_recent_timestamp are set, verify they exist
    if metrics.get('most_recent_run_id') and ledger_path.exists():
        most_recent_run_id = metrics.get('most_recent_run_id')
        found = False
        try:
            with open(ledger_path, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get('run_id') == most_recent_run_id:
                            found = True
                            break
            validation_result['consistency_checks']['most_recent_run_exists'] = found
            if not found:
                validation_result['issues'].append(f"Most recent run_id {most_recent_run_id} not found in ledger")
        except Exception as e:
            validation_result['issues'].append(f"Could not verify most_recent_run in ledger: {str(e)}")

    # Check max_retry_count is non-negative
    max_retry = metrics.get('max_retry_count', 0)
    if max_retry < 0:
        validation_result['issues'].append(f"max_retry_count is negative: {max_retry}")
        validation_result['metrics_valid'] = False

    # Check average_retry_count is non-negative
    avg_retry = metrics.get('average_retry_count', 0)
    if avg_retry < 0:
        validation_result['issues'].append(f"average_retry_count is negative: {avg_retry}")
        validation_result['metrics_valid'] = False

    return validation_result


def main():
    metrics_path = Path(__file__).parent.parent / 'artifacts' / 'metrics' / 'runtime_metrics.json'
    ledger_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_ledger.jsonl'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'validation' / 'runtime_metrics_validation.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    validation_result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'metrics_file': str(metrics_path),
        'ledger_file': str(ledger_path),
        'validations': {},
        'overall_status': 'fail',
        'errors': []
    }

    if not metrics_path.exists():
        validation_result['errors'].append(f"Metrics file not found: {metrics_path}")
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"Metrics validation FAILED: file not found", file=sys.stderr)
        return 1

    try:
        with open(metrics_path) as f:
            metrics = json.load(f)
    except Exception as e:
        validation_result['errors'].append(f"Failed to load metrics: {str(e)}")
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"Metrics validation FAILED: load error", file=sys.stderr)
        return 1

    validation_result['validations']['metrics_validation'] = validate_metrics(metrics, ledger_path)

    if validation_result['validations']['metrics_validation']['metrics_valid']:
        validation_result['overall_status'] = 'pass'
    else:
        validation_result['overall_status'] = 'fail'

    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)

    print(f"Metrics validation complete: {validation_result['overall_status']}")
    print(f"Output: {output_path}")

    return 0 if validation_result['overall_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
