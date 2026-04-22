#!/usr/bin/env python3
"""Integration orchestrator: runs full chain end-to-end."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add bin to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from hardware_design_processor import process_hardware_request
from procurement_evaluator import evaluate_bom
from edition_resolver import resolve_editions
from site_generator import generate_site


def run_integration_chain(output_dir: str = "artifacts/integration_demo") -> dict:
    """Execute full integration chain."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {
        "started_at": datetime.now().isoformat(),
        "stages": {},
        "artifacts": [],
    }

    print("[1/5] Hardware Design Processor...")
    hardware_request = {
        "project_id": "hw-esp32-iot-gateway-v1",
        "name": "IoT Gateway with ESP32-S3",
        "description": "WiFi/BLE gateway for sensor networks",
        "target_platform": "esp32",
        "variant": "esp32-s3",
    }

    try:
        hardware_result = process_hardware_request(hardware_request)
        hardware_file = output_path / "01_hardware_design.json"
        hardware_file.write_text(json.dumps(hardware_result, indent=2))
        results["stages"]["hardware"] = {
            "status": "complete",
            "artifact": str(hardware_file),
            "project_id": hardware_result["project_id"],
            "bom_cost": hardware_result["bom"]["total_cost"],
        }
        results["artifacts"].append(str(hardware_file))
        print(f"   ✓ Generated BOM: {hardware_result['bom']['total_cost']}")
    except Exception as e:
        results["stages"]["hardware"] = {"status": "failed", "error": str(e)}
        print(f"   ✗ Failed: {e}")
        return results

    print("[2/5] Procurement Evaluator...")
    try:
        procurement_result = evaluate_bom(hardware_result["bom"])
        procurement_file = output_path / "02_procurement_evaluation.json"
        procurement_file.write_text(json.dumps(procurement_result, indent=2))
        results["stages"]["procurement"] = {
            "status": "complete",
            "artifact": str(procurement_file),
            "parts_evaluated": len(procurement_result["procurement_decisions"]),
            "total_cost": procurement_result["summary"]["total_procurement_cost"],
        }
        results["artifacts"].append(str(procurement_file))
        print(f"   ✓ Evaluated {len(procurement_result['procurement_decisions'])} parts")
    except Exception as e:
        results["stages"]["procurement"] = {"status": "failed", "error": str(e)}
        print(f"   ✗ Failed: {e}")
        return results

    print("[3/5] Edition Resolver...")
    try:
        edition_result = resolve_editions(hardware_result, procurement_result)
        edition_file = output_path / "03_editions_resolved.json"
        edition_file.write_text(json.dumps(edition_result, indent=2))
        results["stages"]["edition"] = {
            "status": "complete",
            "artifact": str(edition_file),
            "editions_created": len(edition_result["editions"]),
            "platforms": [e["edition"]["target_platform"] for e in edition_result["editions"]],
        }
        results["artifacts"].append(str(edition_file))
        print(f"   ✓ Resolved {len(edition_result['editions'])} editions")
    except Exception as e:
        results["stages"]["edition"] = {"status": "failed", "error": str(e)}
        print(f"   ✗ Failed: {e}")
        return results

    print("[4/5] Website Generator...")
    try:
        site_result = generate_site(edition_result, str(output_path / "site"))
        site_file = output_path / "04_website_generated.json"
        site_file.write_text(json.dumps(site_result, indent=2))
        results["stages"]["website"] = {
            "status": "complete",
            "artifact": str(site_file),
            "pages_generated": len(site_result["generated_pages"]),
            "output_directory": site_result["output_directory"],
        }
        results["artifacts"].extend(site_result["generated_pages"])
        print(f"   ✓ Generated {len(site_result['generated_pages'])} pages")
    except Exception as e:
        results["stages"]["website"] = {"status": "failed", "error": str(e)}
        print(f"   ✗ Failed: {e}")
        return results

    print("[5/5] Integration Summary...")
    summary = {
        "chain_status": "complete",
        "total_stages": 4,
        "successful_stages": 4,
        "hardware_to_website_flow": [
            "Hardware design (BOM)",
            "Procurement evaluation",
            "Edition resolution",
            "Website generation",
        ],
        "data_artifacts": [
            "01_hardware_design.json",
            "02_procurement_evaluation.json",
            "03_editions_resolved.json",
            "04_website_generated.json",
        ],
        "web_artifacts": list(Path(output_path / "site").glob("*.html")) if (output_path / "site").exists() else [],
        "total_cost": procurement_result["summary"]["total_procurement_cost"],
        "editions_available": len(edition_result["editions"]),
        "timestamp": datetime.now().isoformat(),
    }

    summary_file = output_path / "INTEGRATION_SUMMARY.json"
    summary_file.write_text(json.dumps(summary, indent=2, default=str))
    results["artifacts"].append(str(summary_file))
    results["summary"] = summary

    results["completed_at"] = datetime.now().isoformat()

    print(f"\n✓ Integration chain complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Artifacts: {len(results['artifacts'])}")

    return results


if __name__ == "__main__":
    result = run_integration_chain()
    print(json.dumps(result, indent=2, default=str))
