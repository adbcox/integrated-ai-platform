#!/usr/bin/env python3
"""
Compute aggregate runtime metrics from execution ledger (JSONL format).
Reads run_ledger.jsonl and produces runtime_metrics.json with aggregated statistics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def compute_metrics_from_ledger(ledger_path):
    """Read ledger and compute aggregate metrics."""
    metrics = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'ledger_source': str(ledger_path),
        'ledger_entry_count': 0,
        'total_runs': 0,
        'successful_runs': 0,
        'failed_runs': 0,
        'retried_runs': 0,
        'first_pass_success_count': 0,
        'first_pass_success_rate': 0.0,
        'retry_success_count': 0,
        'retry_success_rate': 0.0,
        'average_retry_count': 0.0,
        'max_retry_count': 0,
        'runs_by_profile': defaultdict(int),
        'runs_by_strategy': defaultdict(int),
        'runs_by_final_state': defaultdict(int),
        'validation_pass_count': defaultdict(int),
        'validation_fail_count': defaultdict(int),
        'most_recent_run_id': None,
        'most_recent_timestamp': None,
        'first_run_timestamp': None,
        'artifact_generation_rate': 0.0,
        'validation_pass_rate': {}
    }

    if not ledger_path.exists():
        return metrics

    entries = []
    total_retry_count = 0
    run_ids_seen = set()
    validation_types = set()

    try:
        with open(ledger_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                    metrics['ledger_entry_count'] += 1
                except json.JSONDecodeError:
                    continue

        if not entries:
            return metrics

        # Sort by timestamp to find first and most recent
        entries.sort(key=lambda e: e.get('timestamp', ''))

        # Compute basic counts
        metrics['total_runs'] = len(entries)
        run_ids_seen = {e['run_id'] for e in entries}

        for entry in entries:
            run_id = entry.get('run_id')
            success = entry.get('success', False)
            retry_count = entry.get('retry_count', 0)
            retried = entry.get('retried', False)
            final_state = entry.get('final_state', 'unknown')
            profile = entry.get('selected_profile', 'unknown')
            strategy = entry.get('selected_strategy', 'unknown')
            artifact_paths = entry.get('artifact_paths', [])
            validation_status = entry.get('validation_status', {})

            # Count successes/failures
            if success:
                metrics['successful_runs'] += 1
            else:
                metrics['failed_runs'] += 1

            # Count retried runs
            if retried:
                metrics['retried_runs'] += 1
                if success:
                    metrics['retry_success_count'] += 1
            else:
                if success:
                    metrics['first_pass_success_count'] += 1

            # Track retry stats
            total_retry_count += retry_count
            if retry_count > metrics['max_retry_count']:
                metrics['max_retry_count'] = retry_count

            # Track profile/strategy distribution
            metrics['runs_by_profile'][profile] += 1
            metrics['runs_by_strategy'][strategy] += 1
            metrics['runs_by_final_state'][final_state] += 1

            # Track validation status
            for val_type, val_status in validation_status.items():
                validation_types.add(val_type)
                if val_status == 'pass':
                    metrics['validation_pass_count'][val_type] = metrics['validation_pass_count'].get(val_type, 0) + 1
                else:
                    metrics['validation_fail_count'][val_type] = metrics['validation_fail_count'].get(val_type, 0) + 1

            # Track artifacts
            if len(artifact_paths) > 0:
                pass

            # Update most recent
            if entry.get('timestamp'):
                metrics['most_recent_timestamp'] = entry.get('timestamp')
                metrics['most_recent_run_id'] = run_id

            # Update first timestamp
            if not metrics['first_run_timestamp']:
                metrics['first_run_timestamp'] = entry.get('timestamp')

        # Compute rates
        if metrics['total_runs'] > 0:
            metrics['first_pass_success_rate'] = metrics['first_pass_success_count'] / metrics['total_runs']
            metrics['average_retry_count'] = total_retry_count / metrics['total_runs']

        if metrics['retried_runs'] > 0:
            metrics['retry_success_rate'] = metrics['retry_success_count'] / metrics['retried_runs']

        # Compute artifact generation rate
        artifact_runs = sum(1 for e in entries if len(e.get('artifact_paths', [])) > 0)
        if metrics['total_runs'] > 0:
            metrics['artifact_generation_rate'] = artifact_runs / metrics['total_runs']

        # Compute validation pass rates by type
        for val_type in validation_types:
            pass_count = metrics['validation_pass_count'].get(val_type, 0)
            fail_count = metrics['validation_fail_count'].get(val_type, 0)
            total_val = pass_count + fail_count
            if total_val > 0:
                metrics['validation_pass_rate'][val_type] = pass_count / total_val
            else:
                metrics['validation_pass_rate'][val_type] = 0.0

        # Convert defaultdicts to regular dicts
        metrics['runs_by_profile'] = dict(metrics['runs_by_profile'])
        metrics['runs_by_strategy'] = dict(metrics['runs_by_strategy'])
        metrics['runs_by_final_state'] = dict(metrics['runs_by_final_state'])
        metrics['validation_pass_count'] = dict(metrics['validation_pass_count'])
        metrics['validation_fail_count'] = dict(metrics['validation_fail_count'])

    except Exception as e:
        metrics['error'] = f"Failed to process ledger: {str(e)}"

    return metrics


def main():
    ledger_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_ledger.jsonl'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'metrics' / 'runtime_metrics.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = compute_metrics_from_ledger(ledger_path)

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Runtime metrics computed")
    print(f"Ledger entries: {metrics['ledger_entry_count']}")
    print(f"Total runs: {metrics['total_runs']}")
    print(f"Successful: {metrics['successful_runs']}")
    print(f"Failed: {metrics['failed_runs']}")
    print(f"Retried: {metrics['retried_runs']}")
    print(f"First-pass success rate: {metrics['first_pass_success_rate']:.1%}")
    print(f"Output: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
