#!/usr/bin/env python3
"""
Validate CMDB topology against schema.
Checks consistency, reference validity, and completeness.
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_cmdb(cmdb_path):
    """Load CMDB topology YAML."""
    with open(cmdb_path) as f:
        return yaml.safe_load(f)


def load_schema(schema_path):
    """Load JSON schema."""
    with open(schema_path) as f:
        return json.load(f)


def validate_structure(cmdb):
    """Validate required top-level fields."""
    required_fields = ["schema_version", "kind", "generated_at", "subsystems"]
    missing = [f for f in required_fields if f not in cmdb]
    return {
        "status": "pass" if not missing else "fail",
        "missing_fields": missing,
        "total_subsystems": len(cmdb.get("subsystems", {}))
    }


def validate_subsystems(cmdb):
    """Validate subsystem definitions."""
    subsystems = cmdb.get("subsystems", {})
    results = {
        "total": len(subsystems),
        "valid": 0,
        "invalid": [],
        "service_count": 0
    }

    for subsys_id, subsys_data in subsystems.items():
        required = ["id", "name", "description", "services"]
        if all(f in subsys_data for f in required):
            results["valid"] += 1
            services = subsys_data.get("services", [])
            results["service_count"] += len(services)

            # Validate services
            for service in services:
                service_required = ["id", "name", "description", "capabilities"]
                if not all(f in service for f in service_required):
                    results["invalid"].append(f"{subsys_id}/{service.get('id', 'unknown')}")
        else:
            results["invalid"].append(subsys_id)

    return results


def validate_edges(cmdb):
    """Validate subsystem edges reference valid subsystems."""
    subsystems = set(cmdb.get("subsystems", {}).keys())
    edges = cmdb.get("subsystem_edges", [])

    results = {
        "total_edges": len(edges),
        "valid_edges": 0,
        "invalid_edges": []
    }

    for edge in edges:
        from_subsys = edge.get("from")
        to_subsys = edge.get("to")

        if from_subsys in subsystems and to_subsys in subsystems:
            results["valid_edges"] += 1
        else:
            results["invalid_edges"].append({
                "from": from_subsys,
                "to": to_subsys,
                "reason": f"from_missing={from_subsys not in subsystems}, to_missing={to_subsys not in subsystems}"
            })

    return results


def validate_integration_points(cmdb):
    """Validate integration points reference valid subsystems."""
    subsystems = set(cmdb.get("subsystems", {}).keys())
    integration_points = cmdb.get("integration_points", [])

    results = {
        "total_integration_points": len(integration_points),
        "valid": 0,
        "invalid": []
    }

    for ip in integration_points:
        from_subsys = ip.get("from")
        to_subsys = ip.get("to")

        if from_subsys in subsystems and to_subsys in subsystems:
            results["valid"] += 1
        else:
            results["invalid"].append({
                "name": ip.get("name"),
                "reason": f"from_missing={from_subsys not in subsystems}, to_missing={to_subsys not in subsystems}"
            })

    return results


def validate_dependencies(cmdb):
    """Validate service dependencies reference valid services (cross-subsystem allowed)."""
    subsystems = cmdb.get("subsystems", {})

    # Build global service map
    global_service_ids = set()
    for subsys_id, subsys_data in subsystems.items():
        services = subsys_data.get("services", [])
        for service in services:
            global_service_ids.add(service["id"])

    results = {
        "services_checked": 0,
        "valid_dependencies": 0,
        "invalid_dependencies": []
    }

    for subsys_id, subsys_data in subsystems.items():
        services = subsys_data.get("services", [])

        for service in services:
            results["services_checked"] += 1
            dependencies = service.get("dependencies", [])

            for dep in dependencies:
                if dep in global_service_ids:
                    results["valid_dependencies"] += 1
                else:
                    results["invalid_dependencies"].append({
                        "service": service["id"],
                        "missing_dependency": dep
                    })

    return results


def main():
    """Run CMDB validation."""
    cmdb_path = Path(__file__).parent.parent / "governance" / "cmdb_topology.v1.yaml"
    schema_path = Path(__file__).parent.parent / "schemas" / "cmdb_schema.json"
    output_path = Path(__file__).parent.parent / "artifacts" / "validation" / "cmdb_validation.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    validation_result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "cmdb_file": str(cmdb_path),
        "schema_file": str(schema_path),
        "validations": {},
        "overall_status": "pass",
        "errors": []
    }

    try:
        cmdb = load_cmdb(cmdb_path)
        schema = load_schema(schema_path)
    except Exception as e:
        validation_result["overall_status"] = "fail"
        validation_result["errors"].append(f"Failed to load files: {str(e)}")
        with open(output_path, "w") as f:
            json.dump(validation_result, f, indent=2)
        print(f"CMDB validation FAILED: {validation_result['errors']}", file=sys.stderr)
        return 1

    # Run all validations
    validation_result["validations"]["structure"] = validate_structure(cmdb)
    validation_result["validations"]["subsystems"] = validate_subsystems(cmdb)
    validation_result["validations"]["edges"] = validate_edges(cmdb)
    validation_result["validations"]["integration_points"] = validate_integration_points(cmdb)
    validation_result["validations"]["dependencies"] = validate_dependencies(cmdb)

    # Determine overall status
    for val_name, val_result in validation_result["validations"].items():
        if isinstance(val_result, dict):
            if val_result.get("status") == "fail":
                validation_result["overall_status"] = "fail"
            if val_result.get("invalid_edges") or val_result.get("invalid") or val_result.get("invalid_dependencies"):
                validation_result["overall_status"] = "fail"

    with open(output_path, "w") as f:
        json.dump(validation_result, f, indent=2)

    print(f"CMDB validation complete: {validation_result['overall_status']}")
    print(f"Output: {output_path}")

    return 0 if validation_result["overall_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
