#!/usr/bin/env python3
"""
Execution compiler: transforms roadmap items into execution-control packages.
Reads roadmap item YAML and execution_control_template.yaml, produces compiled instance.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_roadmap_item(item_id):
    """Load a roadmap item by ID."""
    item_path = Path(__file__).parent.parent / 'docs' / 'roadmap' / 'items' / f'{item_id}.yaml'
    if not item_path.exists():
        raise FileNotFoundError(f"Roadmap item not found: {item_path}")
    with open(item_path) as f:
        return yaml.safe_load(f)


def load_template():
    """Load execution control template."""
    template_path = Path(__file__).parent.parent / 'governance' / 'execution_control_template.yaml'
    with open(template_path) as f:
        return yaml.safe_load(f)


def compile_execution_package(roadmap_item, template):
    """Compile a roadmap item into an execution-control package."""
    item_id = roadmap_item['id']

    # Extract template example as baseline
    template_example = template.get('example_template', {})

    # Merge roadmap item fields with template defaults
    compiled = {
        'schema_version': '1.0',
        'kind': 'execution_control_instance',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'execution_id': f'EXEC-{item_id}-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}',
        'roadmap_ids': [item_id],
        'objective': roadmap_item.get('scope', {}).get('objective', 'Execute roadmap item'),
        'scope': {
            'summary': roadmap_item.get('title', 'Roadmap item execution'),
            'in_scope': roadmap_item.get('scope', {}).get('in_scope', []),
            'out_of_scope': roadmap_item.get('scope', {}).get('out_of_scope', [])
        },
        'first_read_files': [
            'CLAUDE.md',
            'AGENTS.md',
            'docs/agent/validation_order.md',
            f'docs/roadmap/items/{item_id}.yaml'
        ],
        'allowed_files': roadmap_item.get('ai_operability', {}).get('allowed_files', []),
        'forbidden_files': roadmap_item.get('ai_operability', {}).get('forbidden_files', []),
        'expected_artifacts': [
            {
                'artifact_type': 'file',
                'path': f'artifacts/execution/{item_id}_completion.json',
                'required': True
            }
        ],
        'validations': [
            {
                'step': 1,
                'name': 'verify_prerequisites',
                'description': 'Verify all first_read_files are readable',
                'gate': 'prerequisites_verified',
                'on_failure': 'halt'
            },
            {
                'step': 2,
                'name': 'verify_allowed_files',
                'description': 'Verify no forbidden_files will be modified',
                'gate': 'file_constraints_verified',
                'on_failure': 'halt'
            },
            {
                'step': 3,
                'name': 'make_check',
                'command': 'make check',
                'description': 'Run full repo syntax validation',
                'gate': 'syntax_validation',
                'on_failure': 'halt'
            },
            {
                'step': 4,
                'name': 'verify_artifacts',
                'description': 'Verify all expected_artifacts exist',
                'gate': 'artifacts_verified',
                'on_failure': 'halt'
            }
        ],
        'rollback_rule': f'Revert all modifications within allowed_files scopes; delete artifacts/execution/{item_id}_* files',
        'completion_rule': 'All validation steps pass, all expected_artifacts exist, roadmap_id preserved in execution record'
    }

    return compiled


def save_compiled_package(compiled_package, item_id):
    """Save compiled execution package to disk."""
    output_dir = Path(__file__).parent.parent / 'artifacts' / 'governance'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'compiled_execution_{item_id}.yaml'

    with open(output_path, 'w') as f:
        yaml.dump(compiled_package, f, default_flow_style=False, sort_keys=False)

    return output_path


def main():
    """Run execution compiler."""
    if len(sys.argv) < 2:
        print("Usage: run_execution_compiler.py <ROADMAP_ID> [<ROADMAP_ID> ...]", file=sys.stderr)
        print("Example: run_execution_compiler.py RM-GOV-004", file=sys.stderr)
        return 1

    roadmap_ids = sys.argv[1:]
    output_results = {}
    output_file = Path(__file__).parent.parent / 'artifacts' / 'governance' / 'execution_compiler_output.json'

    try:
        template = load_template()
    except Exception as e:
        print(f"Error loading template: {e}", file=sys.stderr)
        return 1

    for item_id in roadmap_ids:
        try:
            roadmap_item = load_roadmap_item(item_id)
            compiled = compile_execution_package(roadmap_item, template)
            output_path = save_compiled_package(compiled, item_id)

            output_results[item_id] = {
                'status': 'compiled',
                'output_path': str(output_path),
                'execution_id': compiled['execution_id'],
                'objective': compiled['objective']
            }
            print(f"Compiled {item_id}: {output_path}")

        except FileNotFoundError as e:
            output_results[item_id] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"Error compiling {item_id}: {e}", file=sys.stderr)
        except Exception as e:
            output_results[item_id] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"Unexpected error compiling {item_id}: {e}", file=sys.stderr)

    # Write compiler output summary
    output_file.parent.mkdir(parents=True, exist_ok=True)
    compiler_summary = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'roadmap_ids_requested': roadmap_ids,
        'compilation_results': output_results,
        'success_count': sum(1 for r in output_results.values() if r['status'] == 'compiled'),
        'error_count': sum(1 for r in output_results.values() if r['status'] == 'error')
    }

    with open(output_file, 'w') as f:
        json.dump(compiler_summary, f, indent=2)

    print(f"\nCompiler output: {output_file}")
    return 0 if compiler_summary['error_count'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
