#!/usr/bin/env python3
"""
Phase 0 Closure Validation Script

Validates that all required artifacts exist, are valid, and meet Phase 0
closure requirements. Returns JSON report with validation results.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import yaml

class Phase0ValidationError(Exception):
    """Validation error with context"""
    pass

def load_yaml_safe(file_path):
    """Load YAML file safely with error handling"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise Phase0ValidationError(f"YAML parse error in {file_path}: {e}")
    except FileNotFoundError:
        raise Phase0ValidationError(f"File not found: {file_path}")
    except Exception as e:
        raise Phase0ValidationError(f"Error reading {file_path}: {e}")

def validate_item_files(repo_root):
    """Validate all 6 roadmap item files exist and are valid"""
    items_dir = repo_root / "docs" / "roadmap" / "items"
    required_items = [
        "RM-AUTO-001.yaml",
        "RM-GOV-001.yaml",
        "RM-OPS-005.yaml",
        "RM-OPS-004.yaml",
        "RM-INV-002.yaml",
        "RM-DEV-001.yaml"
    ]

    results = {"items": {}, "all_exist": True, "all_valid": True}

    for item_file in required_items:
        item_path = items_dir / item_file
        check_result = {
            "exists": item_path.exists(),
            "valid": False,
            "status": "valid"
        }

        if not check_result["exists"]:
            results["all_exist"] = False
            check_result["status"] = "missing"
        else:
            try:
                data = load_yaml_safe(item_path)
                if isinstance(data, dict) and "status" in data:
                    check_result["valid"] = True
                    check_result["item_status"] = data.get("status")
                else:
                    check_result["status"] = "invalid_schema"
                    results["all_valid"] = False
            except Phase0ValidationError as e:
                check_result["status"] = "parse_error"
                check_result["error"] = str(e)
                results["all_valid"] = False

        results["items"][item_file] = check_result

    return results

def validate_governance_schemas(repo_root):
    """Validate all required governance schemas exist and are valid"""
    gov_dir = repo_root / "governance"
    required_schemas = [
        "goal_intake_schema.v1.yaml",
        "execution_governance_schema.v1.yaml",
        "telemetry_event_schema.v1.yaml",
        "backup_restore_schema.v1.yaml",
        "asset_inventory_schema.v1.yaml",
        "apple_xcode_workflow.v1.yaml"
    ]

    results = {"schemas": {}, "all_exist": True, "all_valid": True}

    for schema_file in required_schemas:
        schema_path = gov_dir / schema_file
        check_result = {
            "exists": schema_path.exists(),
            "valid": False,
            "status": "valid"
        }

        if not check_result["exists"]:
            results["all_exist"] = False
            check_result["status"] = "missing"
        else:
            try:
                data = load_yaml_safe(schema_path)
                if isinstance(data, dict) and "schema_version" in data:
                    check_result["valid"] = True
                else:
                    check_result["status"] = "invalid_schema"
                    results["all_valid"] = False
            except Phase0ValidationError as e:
                check_result["status"] = "parse_error"
                check_result["error"] = str(e)
                results["all_valid"] = False

        results["schemas"][schema_file] = check_result

    return results

def validate_adrs(repo_root):
    """Validate all 7 ADRs exist and are readable"""
    adr_dir = repo_root / "governance" / "adr"
    required_adrs = [
        "ADR-SESSION-SCHEMA.md",
        "ADR-TOOL-SYSTEM.md",
        "ADR-WORKSPACE-CONTRACT.md",
        "ADR-INFERENCE-GATEWAY.md",
        "ADR-PERMISSION-MODEL.md",
        "ADR-ARTIFACT-BUNDLE.md",
        "ADR-AUTONOMY-SCORECARD.md"
    ]

    results = {"adrs": {}, "all_exist": True, "all_valid": True}

    for adr_file in required_adrs:
        adr_path = adr_dir / adr_file
        check_result = {
            "exists": adr_path.exists(),
            "valid": False,
            "status": "valid"
        }

        if not check_result["exists"]:
            results["all_exist"] = False
            check_result["status"] = "missing"
        else:
            try:
                with open(adr_path, 'r') as f:
                    content = f.read()
                if len(content) > 100:  # Reasonable minimum for an ADR
                    check_result["valid"] = True
                else:
                    check_result["status"] = "insufficient_content"
                    results["all_valid"] = False
            except Exception as e:
                check_result["status"] = "read_error"
                check_result["error"] = str(e)
                results["all_valid"] = False

        results["adrs"][adr_file] = check_result

    return results

def validate_supporting_files(repo_root):
    """Validate supporting files exist and are valid"""
    required_files = [
        ("docs/standards/DEFINITION_OF_DONE.md", "markdown"),
        ("schemas/examples/execution_control_package_example.json", "json"),
        ("governance/cmdb_lite.v1.yaml", "yaml")
    ]

    results = {"files": {}, "all_exist": True, "all_valid": True}

    for file_rel_path, file_type in required_files:
        file_path = repo_root / file_rel_path
        check_result = {
            "exists": file_path.exists(),
            "valid": False,
            "status": "valid"
        }

        if not check_result["exists"]:
            results["all_exist"] = False
            check_result["status"] = "missing"
        else:
            try:
                if file_type == "yaml":
                    data = load_yaml_safe(file_path)
                    check_result["valid"] = data is not None
                elif file_type == "json":
                    with open(file_path, 'r') as f:
                        json.load(f)
                    check_result["valid"] = True
                elif file_type == "markdown":
                    with open(file_path, 'r') as f:
                        content = f.read()
                    check_result["valid"] = len(content) > 100

                if not check_result["valid"]:
                    check_result["status"] = "invalid_format"
                    results["all_valid"] = False
            except Exception as e:
                check_result["status"] = "parse_error"
                check_result["error"] = str(e)
                results["all_valid"] = False

        results["files"][file_rel_path] = check_result

    return results

def validate_roadmap_surfaces(repo_root):
    """Validate roadmap surface files exist and contain expected content"""
    roadmap_dir = repo_root / "docs" / "roadmap"
    required_surfaces = [
        "ROADMAP_STATUS_SYNC.md",
        "ROADMAP_MASTER.md",
        "ROADMAP_INDEX.md"
    ]

    results = {"surfaces": {}, "all_exist": True, "all_valid": True}

    for surface_file in required_surfaces:
        surface_path = roadmap_dir / surface_file
        check_result = {
            "exists": surface_path.exists(),
            "valid": False,
            "status": "valid"
        }

        if not check_result["exists"]:
            results["all_exist"] = False
            check_result["status"] = "missing"
        else:
            try:
                with open(surface_path, 'r') as f:
                    content = f.read()

                # Check for expected content markers
                has_phase0_bundle = any(marker in content for marker in [
                    "Phase 0", "phase0", "closure", "6-item", "bundle"
                ])

                check_result["valid"] = len(content) > 500 and has_phase0_bundle

                if not check_result["valid"]:
                    check_result["status"] = "insufficient_content"
                    results["all_valid"] = False
                    check_result["has_phase0_markers"] = has_phase0_bundle

            except Exception as e:
                check_result["status"] = "read_error"
                check_result["error"] = str(e)
                results["all_valid"] = False

        results["surfaces"][surface_file] = check_result

    return results

def main():
    """Run all validation checks"""
    repo_root = Path(__file__).parent.parent

    print("=" * 70)
    print("PHASE 0 CLOSURE VALIDATION")
    print("=" * 70)
    print()

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo_root": str(repo_root),
        "validation_passes": {}
    }

    # Run validation checks
    print("Validating item files...")
    item_results = validate_item_files(repo_root)
    results["validation_passes"]["item_files"] = item_results
    print(f"  Items: {sum(1 for i in item_results['items'].values() if i['valid'])}/{len(item_results['items'])} valid")

    print("Validating governance schemas...")
    schema_results = validate_governance_schemas(repo_root)
    results["validation_passes"]["governance_schemas"] = schema_results
    print(f"  Schemas: {sum(1 for s in schema_results['schemas'].values() if s['valid'])}/{len(schema_results['schemas'])} valid")

    print("Validating ADRs...")
    adr_results = validate_adrs(repo_root)
    results["validation_passes"]["adrs"] = adr_results
    print(f"  ADRs: {sum(1 for a in adr_results['adrs'].values() if a['valid'])}/{len(adr_results['adrs'])} valid")

    print("Validating supporting files...")
    file_results = validate_supporting_files(repo_root)
    results["validation_passes"]["supporting_files"] = file_results
    print(f"  Files: {sum(1 for f in file_results['files'].values() if f['valid'])}/{len(file_results['files'])} valid")

    print("Validating roadmap surfaces...")
    surface_results = validate_roadmap_surfaces(repo_root)
    results["validation_passes"]["roadmap_surfaces"] = surface_results
    print(f"  Surfaces: {sum(1 for s in surface_results['surfaces'].values() if s['valid'])}/{len(surface_results['surfaces'])} valid")

    # Overall result
    all_passes = all([
        item_results["all_exist"] and item_results["all_valid"],
        schema_results["all_exist"] and schema_results["all_valid"],
        adr_results["all_exist"] and adr_results["all_valid"],
        file_results["all_exist"] and file_results["all_valid"],
        surface_results["all_exist"] and surface_results["all_valid"]
    ])

    results["overall_status"] = "PASS" if all_passes else "FAIL"

    # Write results to file
    validation_dir = repo_root / "artifacts" / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

    output_file = validation_dir / "phase0_closure_validation.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print("=" * 70)
    if all_passes:
        print("RESULT: ✓ ALL VALIDATION CHECKS PASSED")
    else:
        print("RESULT: ✗ VALIDATION FAILED")
        print()
        print("Failed checks:")
        for category, check_results in results["validation_passes"].items():
            if isinstance(check_results, dict):
                for item_name, item_result in check_results.items():
                    if isinstance(item_result, dict) and not item_result.get("valid", True):
                        print(f"  - {category}/{item_name}: {item_result.get('status', 'unknown')}")

    print("=" * 70)
    print(f"Validation report written to: {output_file}")
    print()

    return 0 if all_passes else 1

if __name__ == "__main__":
    sys.exit(main())
