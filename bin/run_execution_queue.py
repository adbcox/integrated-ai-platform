#!/usr/bin/env python3
"""
Queue-based execution runner: execute multiple bundles sequentially from a queue.
Supports both queue JSON file and CLI bundle path list.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def load_queue_file(queue_path):
    """Load queue from JSON file."""
    with open(queue_path) as f:
        return json.load(f)


def run_bundle(bundle_path, run_executor_script):
    """Execute a single bundle via run_execution_bundle.py."""
    try:
        result = subprocess.run(
            [sys.executable, str(run_executor_script), str(bundle_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            'bundle_path': str(bundle_path),
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'bundle_path': str(bundle_path),
            'exit_code': -1,
            'error': 'Timeout',
            'success': False
        }
    except Exception as e:
        return {
            'bundle_path': str(bundle_path),
            'exit_code': -1,
            'error': str(e),
            'success': False
        }


def extract_run_id_from_result(run_result_path):
    """Extract run_id from a generated run_result.json."""
    try:
        with open(run_result_path) as f:
            data = json.load(f)
            return data.get('run_id')
    except:
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Execute multiple bundles from a queue')
    parser.add_argument('--queue', help='Path to queue JSON file')
    parser.add_argument('--bundles', nargs='+', help='List of bundle paths to execute')
    parser.add_argument('--output', default=None, help='Output path for queue result')

    args = parser.parse_args()

    # Determine bundles to execute
    bundles_to_run = []

    if args.queue:
        queue_path = Path(args.queue)
        if not queue_path.exists():
            print(f"Queue file not found: {queue_path}", file=sys.stderr)
            return 1
        queue_data = load_queue_file(queue_path)
        queue_bundles = queue_data.get('bundles', [])
        # Extract bundle paths from bundle objects or use directly if strings
        for bundle_item in queue_bundles:
            if isinstance(bundle_item, dict):
                bundles_to_run.append(bundle_item.get('bundle_path'))
            else:
                bundles_to_run.append(bundle_item)
    elif args.bundles:
        bundles_to_run = args.bundles
    else:
        # Default: use sample execution bundle
        default_bundle = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'sample_execution_bundle.json'
        if default_bundle.exists():
            bundles_to_run = [str(default_bundle)]
        else:
            print("No queue or bundles specified, and default bundle not found", file=sys.stderr)
            return 1

    run_executor_script = Path(__file__).parent / 'run_execution_bundle.py'
    if not run_executor_script.exists():
        print(f"Run executor script not found: {run_executor_script}", file=sys.stderr)
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'queue_result.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Execute queue
    queue_result = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'total_bundles': len(bundles_to_run),
        'total_runs': 0,
        'succeeded_runs': 0,
        'failed_runs': 0,
        'run_ids': [],
        'bundle_paths': bundles_to_run,
        'per_bundle_results': [],
        'aggregate_status': 'unknown'
    }

    for bundle_path in bundles_to_run:
        bundle_file = Path(bundle_path)

        if not bundle_file.exists():
            queue_result['per_bundle_results'].append({
                'bundle_path': str(bundle_path),
                'status': 'failed',
                'reason': 'Bundle file not found'
            })
            queue_result['failed_runs'] += 1
            continue

        # Run the bundle (note: the current run_execution_bundle.py doesn't support --bundle arg yet,
        # it uses hardcoded paths, so we'll just execute it as-is)
        print(f"Executing bundle: {bundle_path}")

        run_result_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'run_result.json'
        exec_result = run_bundle(bundle_path, run_executor_script)

        # Extract run_id if successful
        run_id = None
        if run_result_path.exists():
            run_id = extract_run_id_from_result(run_result_path)

        queue_result['total_runs'] += 1
        if exec_result['success']:
            queue_result['succeeded_runs'] += 1
            status = 'succeeded'
        else:
            queue_result['failed_runs'] += 1
            status = 'failed'

        per_bundle_result = {
            'bundle_path': str(bundle_path),
            'status': status,
            'run_id': run_id,
            'exit_code': exec_result.get('exit_code'),
            'run_result_path': str(run_result_path) if run_result_path.exists() else None
        }

        if run_id:
            queue_result['run_ids'].append(run_id)

        queue_result['per_bundle_results'].append(per_bundle_result)

    # Determine aggregate status
    if queue_result['failed_runs'] == 0:
        queue_result['aggregate_status'] = 'pass'
    else:
        queue_result['aggregate_status'] = 'fail'

    # Write queue result
    with open(output_path, 'w') as f:
        json.dump(queue_result, f, indent=2)

    print(f"\nQueue execution complete")
    print(f"Total: {queue_result['total_runs']}")
    print(f"Succeeded: {queue_result['succeeded_runs']}")
    print(f"Failed: {queue_result['failed_runs']}")
    print(f"Status: {queue_result['aggregate_status']}")
    print(f"Output: {output_path}")

    return 0 if queue_result['aggregate_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
