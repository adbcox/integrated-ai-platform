#!/usr/bin/env python3
"""
Roadmap-to-Execution Compiler

Compiles roadmap items into execution-ready bundles with governance and scope preservation.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

ROADMAP_ITEMS_DIR = Path(__file__).parent.parent / "docs/roadmap/items"
ARCHITECTURE_FILE = (
    Path(__file__).parent.parent / "governance/canonical_architecture_baseline.yaml"
)
BUNDLE_OUTPUT_DIR = Path(__file__).parent.parent / "artifacts/compiled_bundles"


def load_roadmap_item(roadmap_id: str) -> Optional[dict]:
    """Load a single roadmap item by ID."""
    item_file = ROADMAP_ITEMS_DIR / f"{roadmap_id}.yaml"
    if not item_file.exists():
        return None

    try:
        with open(item_file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {roadmap_id}: {e}", file=sys.stderr)
        return None


def load_architecture() -> Optional[dict]:
    """Load canonical architecture baseline."""
    if not ARCHITECTURE_FILE.exists():
        return None

    try:
        with open(ARCHITECTURE_FILE) as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def find_subsystems_for_item(item: dict, architecture: Optional[dict]) -> list:
    """Find subsystems affected by this roadmap item."""
    if not architecture:
        return []

    subsystems = []
    # Check CMDB refs in item
    cmdb_refs = item.get("cmdb", {}).get("refs", [])
    arch_subsystems = architecture.get("subsystems", [])

    for ref in cmdb_refs:
        if ref.startswith("subsystem:"):
            subsystem_name = ref.replace("subsystem:", "")
            for subsys in arch_subsystems:
                if subsys.get("name") == subsystem_name:
                    subsystems.append(
                        {
                            "subsystem_id": subsys.get("subsystem_id"),
                            "subsystem_name": subsys.get("name"),
                            "interaction_type": "modified_by",
                        }
                    )
                    break

    return subsystems


def compile_bundle(roadmap_id: str, item: dict, architecture: Optional[dict]) -> dict:
    """Compile a roadmap item into an execution bundle."""
    now = datetime.utcnow().isoformat() + "Z"

    bundle = {
        "schema_version": "1.0",
        "kind": "execution_bundle",
        "bundle_id": f"BUNDLE-{roadmap_id}-COMPILED-{datetime.utcnow().strftime('%Y%m%d')}",
        "roadmap_id": roadmap_id,
        "roadmap_title": item.get("title", ""),
        "generated_at": now,
        "compiled_from": "roadmap_compiler.py v1.0",
        "objective": item.get("scope", {}).get("objective", ""),
        "scope": {
            "in_scope": item.get("scope", {}).get("in_scope", []),
            "out_of_scope": item.get("scope", {}).get("out_of_scope", []),
        },
        "subsystem_scope": find_subsystems_for_item(item, architecture),
        "allowed_files": item.get("ai_operability", {}).get("allowed_files", []),
        "forbidden_files": item.get("ai_operability", {}).get("forbidden_files", []),
        "validation_order": [
            {
                "step": i + 1,
                "name": f"validation_step_{i+1}",
                "command": cmd,
                "gates": [f"gate_{i+1}"],
                "on_failure": "halt",
            }
            for i, cmd in enumerate(
                item.get("ai_operability", {}).get("validation_order", [])
            )
        ],
        "rollback_rule": item.get("ai_operability", {}).get("rollback_rule", ""),
        "expected_artifacts": [
            {"artifact_type": art, "location": "artifacts/", "required": True}
            for art in item.get("ai_operability", {}).get("artifact_outputs", [])
        ],
        "execution_instructions": {
            "objective": item.get("scope", {}).get("objective", ""),
            "constraints": [
                f"modify only files in allowed_files",
                f"preserve all rollback capability",
                f"validate after each phase",
            ],
            "allowed_modification_patterns": [
                "add function",
                "modify existing function",
                "add import",
                "modify configuration",
            ],
            "suggested_approach": item.get("ai_operability", {}).get(
                "developer_intent", ""
            ),
            "validation_gates": [
                f"gate_{i+1}"
                for i in range(
                    len(item.get("ai_operability", {}).get("validation_order", []))
                )
            ],
        },
        "roadmap_fields_preserved": {
            "category": item.get("category", ""),
            "priority": item.get("priority", ""),
            "phase_target": item.get("governance", {}).get("phase_target", ""),
            "status": item.get("status", ""),
        },
        "compilation_metadata": {
            "compiler_version": "1.0",
            "dependency_planner_state": {
                "unblocked_at_compile": True,
                "blockers_resolved": [],
            },
            "subsystem_bindings": [
                s["subsystem_id"]
                for s in find_subsystems_for_item(item, architecture)
            ],
        },
    }

    return bundle


def main():
    if len(sys.argv) < 2:
        print("Usage: roadmap_compiler.py <roadmap_id> [--output <file>]", file=sys.stderr)
        sys.exit(1)

    roadmap_id = sys.argv[1]
    output_file = None

    if len(sys.argv) >= 4 and sys.argv[2] == "--output":
        output_file = sys.argv[3]

    # Load roadmap item
    item = load_roadmap_item(roadmap_id)
    if not item:
        print(f"Error: Could not load roadmap item {roadmap_id}", file=sys.stderr)
        sys.exit(1)

    # Load architecture
    architecture = load_architecture()

    # Compile bundle
    bundle = compile_bundle(roadmap_id, item, architecture)

    # Output
    if output_file:
        BUNDLE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = BUNDLE_OUTPUT_DIR / output_file
        with open(output_path, "w") as f:
            json.dump(bundle, f, indent=2)
        print(f"Bundle compiled to {output_path}")
    else:
        print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    main()
