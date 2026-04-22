#!/usr/bin/env python3
"""
Planner-compiler pipeline: automated end-to-end execution path.
Runs dependency planner, selects next item, compiles it automatically.
"""

import json
import subprocess
import sys
import yaml
from pathlib import Path
from datetime import datetime


def run_planner():
    """Execute dependency planner."""
    result = subprocess.run(
        ['python3', 'bin/run_dependency_planner.py'],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr


def load_planner_output():
    """Load planner output and extract chosen item."""
    output_path = Path(__file__).parent.parent / 'artifacts' / 'governance' / 'dependency_planner_output.json'
    with open(output_path) as f:
        data = json.load(f)
    return data


def run_compiler(roadmap_id):
    """Execute execution compiler for selected item."""
    result = subprocess.run(
        ['python3', 'bin/run_execution_compiler.py', roadmap_id],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr


def load_compiled_package(roadmap_id):
    """Load compiled execution package."""
    pkg_path = Path(__file__).parent.parent / 'artifacts' / 'governance' / f'compiled_execution_{roadmap_id}.yaml'
    if not pkg_path.exists():
        return None
    with open(pkg_path) as f:
        return yaml.safe_load(f)


def main():
    """Run end-to-end planner-compiler pipeline."""
    pipeline_dir = Path(__file__).parent.parent / 'artifacts' / 'governance'
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    pipeline_artifact_path = pipeline_dir / 'planner_compiler_pipeline.json'
    proof_artifact_path = pipeline_dir / 'pipeline_execution_proof.json'

    pipeline_result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'pipeline_success': False,
        'failure_reason': '',
        'planner_artifact': None,
        'chosen_next_item': None,
        'compiler_artifact': None,
        'compiled_execution_package': None
    }

    # Step 1: Run planner
    planner_ok, planner_stdout, planner_stderr = run_planner()
    if not planner_ok:
        pipeline_result['failure_reason'] = f'Planner failed: {planner_stderr}'
        with open(pipeline_artifact_path, 'w') as f:
            json.dump(pipeline_result, f, indent=2)
        print(f"Pipeline failed: {pipeline_result['failure_reason']}", file=sys.stderr)
        return 1

    # Step 2: Load planner output and extract chosen item
    try:
        planner_output = load_planner_output()
        chosen_item = planner_output.get('chosen_next_item')
        if not chosen_item:
            pipeline_result['failure_reason'] = 'Planner did not output chosen_next_item'
            with open(pipeline_artifact_path, 'w') as f:
                json.dump(pipeline_result, f, indent=2)
            print(f"Pipeline failed: {pipeline_result['failure_reason']}", file=sys.stderr)
            return 1
    except Exception as e:
        pipeline_result['failure_reason'] = f'Failed to load planner output: {str(e)}'
        with open(pipeline_artifact_path, 'w') as f:
            json.dump(pipeline_result, f, indent=2)
        print(f"Pipeline failed: {pipeline_result['failure_reason']}", file=sys.stderr)
        return 1

    pipeline_result['planner_artifact'] = 'artifacts/governance/dependency_planner_output.json'
    pipeline_result['chosen_next_item'] = chosen_item

    # Step 3: Run compiler for chosen item
    compiler_ok, compiler_stdout, compiler_stderr = run_compiler(chosen_item)
    if not compiler_ok:
        pipeline_result['failure_reason'] = f'Compiler failed for {chosen_item}: {compiler_stderr}'
        with open(pipeline_artifact_path, 'w') as f:
            json.dump(pipeline_result, f, indent=2)
        print(f"Pipeline failed: {pipeline_result['failure_reason']}", file=sys.stderr)
        return 1

    # Step 4: Verify compiled package exists
    compiled_pkg = load_compiled_package(chosen_item)
    if not compiled_pkg:
        pipeline_result['failure_reason'] = f'Compiled package not found for {chosen_item}'
        with open(pipeline_artifact_path, 'w') as f:
            json.dump(pipeline_result, f, indent=2)
        print(f"Pipeline failed: {pipeline_result['failure_reason']}", file=sys.stderr)
        return 1

    pipeline_result['compiler_artifact'] = 'artifacts/governance/execution_compiler_output.json'
    pipeline_result['compiled_execution_package'] = f'artifacts/governance/compiled_execution_{chosen_item}.yaml'
    pipeline_result['pipeline_success'] = True

    # Step 5: Generate execution readiness proof
    proof = generate_execution_readiness_proof(chosen_item, compiled_pkg)

    # Step 6: Write artifacts
    with open(pipeline_artifact_path, 'w') as f:
        json.dump(pipeline_result, f, indent=2)

    with open(proof_artifact_path, 'w') as f:
        json.dump(proof, f, indent=2)

    print(f"Pipeline success: {chosen_item} compiled and validated")
    print(f"Pipeline artifact: {pipeline_artifact_path}")
    print(f"Proof artifact: {proof_artifact_path}")

    return 0


def generate_execution_readiness_proof(roadmap_id, compiled_pkg):
    """Verify compiled execution package is execution-ready."""
    required_fields = [
        'roadmap_ids', 'objective', 'first_read_files', 'allowed_files',
        'forbidden_files', 'expected_artifacts', 'validations',
        'rollback_rule', 'completion_rule'
    ]

    field_results = {}
    path_check_results = {}
    all_fields_present = True
    all_fields_nonempty = True

    # Check required fields exist
    for field in required_fields:
        present = field in compiled_pkg
        field_results[field] = {
            'present': present,
            'nonempty': bool(compiled_pkg.get(field)) if present else False,
            'value_type': type(compiled_pkg.get(field)).__name__ if present else 'missing'
        }
        if not present:
            all_fields_present = False
        if present and not compiled_pkg.get(field):
            all_fields_nonempty = False

    # Check roadmap_ids contains selected item
    roadmap_ids = compiled_pkg.get('roadmap_ids', [])
    roadmap_contains_item = roadmap_id in roadmap_ids

    # Check first_read_files are readable (or reasonable)
    first_read = compiled_pkg.get('first_read_files', [])
    for frf in first_read:
        path = Path(__file__).parent.parent / frf
        exists = path.exists()
        path_check_results[f'first_read_file:{frf}'] = {'exists': exists, 'path': str(path)}

    # Summary
    final_status = 'execution_ready' if (
        all_fields_present and all_fields_nonempty and roadmap_contains_item
    ) else 'incomplete'

    return {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'selected_item': roadmap_id,
        'compiled_package_path': f'artifacts/governance/compiled_execution_{roadmap_id}.yaml',
        'field_check_results': field_results,
        'path_check_results': path_check_results,
        'roadmap_id_in_package': roadmap_contains_item,
        'final_status': final_status
    }


if __name__ == '__main__':
    sys.exit(main())
