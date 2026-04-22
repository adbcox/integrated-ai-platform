#!/usr/bin/env python3
"""
Validate session/job runtime contract schema and example instance.
Loads schema, loads example, validates example against schema.
Outputs validation result to artifacts/examples/validation_result.json.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: jsonschema package not installed. Install with: pip install jsonschema")
    sys.exit(1)


def load_json(path: str) -> dict:
    """Load and parse JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


def validate_example(schema: dict, example: dict) -> dict:
    """
    Validate example against schema.
    Returns dict with validation result, any errors, and metadata.
    """
    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "schema_file": "schemas/session_job_schema.v1.json",
        "example_file": "artifacts/examples/session_run_example.json",
        "validation_status": "unknown",
        "errors": [],
        "warnings": [],
        "metrics": {
            "schema_properties_count": len(schema.get("properties", {})),
            "example_keys_count": len(example.keys()),
            "required_fields": schema.get("required", []),
        }
    }

    try:
        # Validate using Draft7 validator
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(example))

        if errors:
            result["validation_status"] = "failed"
            for error in errors:
                result["errors"].append({
                    "message": error.message,
                    "path": list(error.absolute_path),
                    "schema_path": list(error.absolute_schema_path)
                })
            return result

        # Check all required fields are present
        missing_fields = []
        for required_field in schema.get("required", []):
            if required_field not in example:
                missing_fields.append(required_field)

        if missing_fields:
            result["validation_status"] = "failed"
            result["errors"].append({
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "path": [],
                "schema_path": ["required"]
            })
            return result

        # Validation successful
        result["validation_status"] = "success"
        result["metrics"]["required_fields_present"] = len(schema.get("required", []))
        result["metrics"]["total_fields_validated"] = len(example.keys())

        return result

    except Exception as e:
        result["validation_status"] = "failed"
        result["errors"].append({
            "message": f"Validation error: {str(e)}",
            "path": [],
            "schema_path": []
        })
        return result


def main():
    """Main validation entry point."""
    try:
        # Load schema and example (or use argument)
        schema = load_json("schemas/session_job_schema.v1.json")
        example_path = sys.argv[1] if len(sys.argv) > 1 else "artifacts/examples/session_run_example.json"
        example = load_json(example_path)

        # Validate
        result = validate_example(schema, example)

        # Ensure artifacts directory exists
        Path("artifacts/examples").mkdir(parents=True, exist_ok=True)

        # Write result
        with open("artifacts/examples/validation_result.json", "w") as f:
            json.dump(result, f, indent=2)

        # Print result to stdout
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        if result["validation_status"] == "success":
            print("\n✓ Validation PASSED: example validates against schema", file=sys.stderr)
            return 0
        else:
            print("\n✗ Validation FAILED", file=sys.stderr)
            for error in result["errors"]:
                print(f"  - {error['message']}", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
