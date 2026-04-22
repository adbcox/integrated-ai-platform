#!/usr/bin/env python3
"""
Dependency planner: evaluates roadmap graph to determine eligible items for next pull.
Reads governance/roadmap_graph.v1.yaml and classifies nodes as eligible/blocked/unknown.
"""

import json
import sys
import yaml
from pathlib import Path


def load_graph(graph_path):
    """Load roadmap dependency graph."""
    with open(graph_path) as f:
        return yaml.safe_load(f)


def load_registry(registry_path):
    """Load roadmap registry for status lookups."""
    try:
        with open(registry_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None


def classify_nodes(graph, registry):
    """Classify each node as eligible, blocked, or unknown."""
    nodes = {node['id']: node for node in graph.get('nodes', [])}
    edges = graph.get('edges', [])

    # Build dependency map: node -> [hard_dependencies]
    dependencies = {node_id: [] for node_id in nodes}
    for edge in edges:
        if edge.get('type') == 'hard':
            dependencies[edge['to']].append(edge['from'])

    # Registry lookup
    registry_status = {}
    if registry:
        for item in registry.get('items', []):
            registry_status[item['id']] = item.get('status')

    classification = {}
    for node_id, node in nodes.items():
        hard_deps = dependencies.get(node_id, [])

        if not hard_deps:
            status = 'eligible'
            reason = 'no hard dependencies'
        else:
            # Check if all hard dependencies are complete/satisfied
            all_satisfied = True
            unsatisfied = []
            for dep_id in hard_deps:
                if dep_id not in nodes:
                    all_satisfied = False
                    unsatisfied.append(f"{dep_id} (missing from graph)")
                else:
                    dep_node = nodes[dep_id]
                    dep_status = dep_node.get('status', 'unknown')
                    if dep_status not in ['complete', 'completed', 'complete', 'in_validation']:
                        all_satisfied = False
                        unsatisfied.append(f"{dep_id} (status: {dep_status})")

            if all_satisfied:
                status = 'eligible'
                reason = f'all {len(hard_deps)} hard dependencies satisfied'
            else:
                status = 'blocked'
                reason = f'blocked by: {", ".join(unsatisfied)}'

        classification[node_id] = {
            'id': node_id,
            'title': node.get('title'),
            'status': node.get('status'),
            'category': node.get('category'),
            'priority': node.get('priority'),
            'dependencies': hard_deps,
            'eligible_for_pull': status == 'eligible',
            'classification': status,
            'reason': reason
        }

    return classification


def generate_candidates(classification):
    """Generate ordered list of eligible candidates for next pull."""
    eligible = [
        (node_id, data) for node_id, data in classification.items()
        if data['eligible_for_pull']
    ]
    # Sort by priority (P1 first), then by category order
    category_order = {'GOV': 0, 'CORE': 1, 'AUTO': 2, 'DEV': 3, 'INTEL': 4}
    eligible.sort(key=lambda x: (
        x[1]['priority'] != 'P1',  # P1 first
        category_order.get(x[1]['category'], 99),
        x[0]
    ))
    return [node_id for node_id, _ in eligible]


def main():
    """Run dependency planner."""
    graph_path = Path(__file__).parent.parent / 'governance' / 'roadmap_graph.v1.yaml'
    registry_path = Path(__file__).parent.parent / 'docs' / 'roadmap' / 'data' / 'roadmap_registry.yaml'
    output_path = Path(__file__).parent.parent / 'artifacts' / 'governance' / 'dependency_planner_output.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        graph = load_graph(graph_path)
        registry = load_registry(registry_path)
    except Exception as e:
        print(f"Error loading graph or registry: {e}", file=sys.stderr)
        return 1

    classification = classify_nodes(graph, registry)
    candidates = generate_candidates(classification)

    # Summary statistics
    eligible_count = sum(1 for data in classification.values() if data['eligible_for_pull'])
    blocked_count = sum(1 for data in classification.values() if data['classification'] == 'blocked')
    chosen_next = candidates[0] if candidates else None

    output = {
        'generated_at': '2026-04-22T02:00:00Z',
        'planner_summary': {
            'total_nodes': len(classification),
            'eligible_count': eligible_count,
            'blocked_count': blocked_count,
            'next_pull_sequence': candidates[:3]  # Top 3 candidates
        },
        'nodes': classification,
        'next_pull_candidates': candidates,
        'chosen_next_item': chosen_next
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Planner output: {output_path}")
    print(f"Eligible items: {eligible_count}/{len(classification)}")
    print(f"Next pull candidates: {candidates[:3]}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
