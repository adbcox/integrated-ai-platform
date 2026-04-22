#!/usr/bin/env python3
"""
Compile execution bundle from roadmap items.
Takes dependency graph output and creates executable bundle definition.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_graph(graph_path):
    """Load roadmap dependency graph."""
    with open(graph_path) as f:
        return yaml.safe_load(f)


def load_cmdb(cmdb_path):
    """Load CMDB topology."""
    with open(cmdb_path) as f:
        return yaml.safe_load(f)


def compile_bundle_for_items(roadmap_ids, graph, cmdb):
    """Compile execution bundle for selected items."""
    nodes = {node['id']: node for node in graph.get('nodes', [])}

    # Validate that all requested items exist
    missing_items = [rid for rid in roadmap_ids if rid not in nodes]
    if missing_items:
        return None, f"Missing roadmap items: {missing_items}"

    # Get all transitive hard dependencies (closure)
    def get_all_hard_deps(item_id, nodes_dict, edges):
        visited = set()
        to_visit = [item_id]
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for edge in edges:
                if edge.get('type') == 'hard' and edge['to'] == current:
                    to_visit.append(edge['from'])
        return visited - {item_id}

    edges = graph.get('edges', [])
    all_items = set(roadmap_ids)
    for rid in roadmap_ids:
        deps = get_all_hard_deps(rid, nodes, edges)
        all_items.update(deps)

    # Build bundle
    objective = f"Implement {len(roadmap_ids)} roadmap items: {', '.join(roadmap_ids)}"

    bundle = {
        'roadmap_ids': sorted(list(all_items)),
        'primary_items': roadmap_ids,
        'objective': objective,
        'description': f"Execute {len(roadmap_ids)} items with {len(all_items) - len(roadmap_ids)} transitive dependencies",
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'allowed_files': [
            'governance/**',
            'bin/**',
            'schemas/**',
            'docs/roadmap/**',
            'artifacts/**'
        ],
        'forbidden_files': [
            'framework/**',
            'tests/**',
            '.github/**',
            'config/routing.yaml',  # governance-controlled routing
            'policies/**'
        ],
        'expected_artifacts': [
            {
                'path': 'artifacts/planning/next_pull.json',
                'type': 'generated',
                'required': True,
                'description': 'Next pull computation output'
            },
            {
                'path': 'artifacts/execution/sample_execution_bundle.json',
                'type': 'generated',
                'required': True,
                'description': 'Compiled execution bundle'
            },
            {
                'path': 'artifacts/validation/cmdb_validation.json',
                'type': 'generated',
                'required': False,
                'description': 'CMDB validation results'
            }
        ],
        'validation_steps': [
            {
                'name': 'YAML syntax validation',
                'command': 'make check',
                'expected_exit_code': 0,
                'description': 'Validate all modified YAML files'
            },
            {
                'name': 'CMDB validation',
                'command': 'python3 bin/validate_cmdb.py',
                'expected_exit_code': 0,
                'description': 'Validate CMDB topology consistency'
            },
            {
                'name': 'Next pull computation',
                'command': 'python3 bin/compute_next_pull.py',
                'expected_exit_code': 0,
                'description': 'Compute eligible next items'
            },
            {
                'name': 'Orchestration validation',
                'command': 'python3 bin/validate_orchestration.py',
                'expected_exit_code': 0,
                'description': 'Validate orchestration model'
            }
        ],
        'rollback_rule': 'Git checkout modified files, remove generated artifacts under artifacts/',
        'completion_rule': 'All validation steps pass, all expected_artifacts exist, next_pull.json is non-empty, orchestration model validated',
        'cmdb_integration': {
            'cmdb_file': 'governance/cmdb_topology.v1.yaml',
            'subsystems_used': list(cmdb.get('subsystems', {}).keys()),
            'integration_points': len(cmdb.get('integration_points', []))
        },
        'execution_notes': [
            'All items share RM-INV-004 CMDB topology as foundation',
            'Hard dependencies must be satisfied before execution',
            'Validation uses real file I/O; no mocking',
            'Orchestration model governs execution lifecycle'
        ]
    }

    return bundle, None


def main():
    """Compile execution bundle."""
    graph_path = Path(__file__).parent.parent / 'governance' / 'roadmap_dependency_graph.v1.yaml'
    cmdb_path = Path(__file__).parent.parent / 'governance' / 'cmdb_topology.v1.yaml'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'execution' / 'sample_execution_bundle.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        graph = load_graph(graph_path)
        cmdb = load_cmdb(cmdb_path)
    except Exception as e:
        print(f"Error loading files: {e}", file=sys.stderr)
        return 1

    # Compile for all 6 items in foundation layer
    roadmap_ids = ['RM-INV-004', 'RM-GOV-004', 'RM-AUTO-002']

    bundle, error = compile_bundle_for_items(roadmap_ids, graph, cmdb)

    if error:
        print(f"Compilation error: {error}", file=sys.stderr)
        return 1

    with open(output_path, 'w') as f:
        json.dump(bundle, f, indent=2)

    print(f"Bundle compilation complete")
    print(f"Primary items: {len(bundle['primary_items'])}")
    print(f"Total items (with deps): {len(bundle['roadmap_ids'])}")
    print(f"Validation steps: {len(bundle['validation_steps'])}")
    print(f"Output: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
