#!/usr/bin/env python3
"""Hardware design processor: generates BOM from hardware requirements."""

import json
import sys
from datetime import datetime
from pathlib import Path


def create_bom_for_esp32(project_id: str, variant: str = "esp32-s3") -> dict:
    """Generate BOM for ESP32-based hardware."""
    bom_components = [
        {
            "part_number": "ESP32-S3-WROOM-1-N8",
            "description": f"ESP32-S3 Module ({variant})",
            "quantity": 1,
            "unit_cost": 4.50,
            "supplier": "Espressif",
            "lead_time_days": 5,
        },
        {
            "part_number": "AMS1117-3V3",
            "description": "3.3V Linear Regulator",
            "quantity": 1,
            "unit_cost": 0.25,
            "supplier": "AMS",
            "lead_time_days": 3,
        },
        {
            "part_number": "TDK-C1206X5R1V106M",
            "description": "Capacitor 10uF 25V 1206",
            "quantity": 5,
            "unit_cost": 0.08,
            "supplier": "TDK",
            "lead_time_days": 2,
        },
        {
            "part_number": "Vishay-CRCW0805100K",
            "description": "Resistor 100k Ohm 0805",
            "quantity": 10,
            "unit_cost": 0.01,
            "supplier": "Vishay",
            "lead_time_days": 2,
        },
        {
            "part_number": "JST-XH-2.54mm",
            "description": "JST XH Connector 2.54mm pitch",
            "quantity": 3,
            "unit_cost": 0.15,
            "supplier": "JST",
            "lead_time_days": 4,
        },
        {
            "part_number": "PCB-FR4-ESP32-BOARD",
            "description": "PCB Board FR4 1.6mm double-sided",
            "quantity": 1,
            "unit_cost": 2.50,
            "supplier": "JLC PCB",
            "lead_time_days": 7,
        },
    ]

    total_cost = sum(c["quantity"] * c["unit_cost"] for c in bom_components)

    return {
        "project_id": project_id,
        "components": bom_components,
        "total_cost": round(total_cost, 2),
        "sourcing_notes": f"ESP32-based design using {variant} variant. Components sourced from major distributors. Lead time critical path: PCB layout (7 days).",
    }


def create_bom_for_nordic(project_id: str, variant: str = "nrf52840") -> dict:
    """Generate BOM for Nordic nRF-based hardware."""
    bom_components = [
        {
            "part_number": f"NORDIC-{variant}",
            "description": f"Nordic {variant} Processor",
            "quantity": 1,
            "unit_cost": 6.75,
            "supplier": "Nordic Semiconductor",
            "lead_time_days": 7,
        },
        {
            "part_number": "NRF52840-32kHz-XTAL",
            "description": "32 kHz Crystal Oscillator",
            "quantity": 1,
            "unit_cost": 0.45,
            "supplier": "Abracon",
            "lead_time_days": 4,
        },
        {
            "part_number": "NRF52840-ANTENNA-PCB",
            "description": "Onboard PCB Antenna for BLE",
            "quantity": 1,
            "unit_cost": 0.10,
            "supplier": "Design",
            "lead_time_days": 1,
        },
        {
            "part_number": "MURATA-BLM18PG221SN1D",
            "description": "Ferrite Bead SMD",
            "quantity": 2,
            "unit_cost": 0.08,
            "supplier": "Murata",
            "lead_time_days": 3,
        },
        {
            "part_number": "TDK-MLZ2012M0R6S",
            "description": "Chip Inductor 0.6uH",
            "quantity": 2,
            "unit_cost": 0.12,
            "supplier": "TDK",
            "lead_time_days": 3,
        },
        {
            "part_number": "BATTERY-CR2032",
            "description": "Coin Cell Battery",
            "quantity": 1,
            "unit_cost": 0.75,
            "supplier": "Panasonic",
            "lead_time_days": 5,
        },
        {
            "part_number": "PCB-FR4-NORDIC-BOARD",
            "description": "PCB Board FR4 1.6mm double-sided",
            "quantity": 1,
            "unit_cost": 3.00,
            "supplier": "JLC PCB",
            "lead_time_days": 7,
        },
    ]

    total_cost = sum(c["quantity"] * c["unit_cost"] for c in bom_components)

    return {
        "project_id": project_id,
        "components": bom_components,
        "total_cost": round(total_cost, 2),
        "sourcing_notes": f"Nordic {variant}-based design with BLE connectivity. Optimized for low-power battery operation. Lead time critical: Crystal oscillator and PCB layout.",
    }


def process_hardware_request(request_data: dict) -> dict:
    """Process hardware design request and generate BOM."""
    project_id = request_data.get("project_id", f"hw-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    target_platform = request_data.get("target_platform", "esp32").lower()
    variant = request_data.get("variant", "esp32-s3" if target_platform == "esp32" else "nrf52840")

    # Generate appropriate BOM based on platform
    if target_platform == "esp32":
        bom = create_bom_for_esp32(project_id, variant)
    elif target_platform in ["nrf52840", "nrf5340", "nordic"]:
        bom = create_bom_for_nordic(project_id, variant)
    else:
        raise ValueError(f"Unsupported platform: {target_platform}")

    # Create design assistant output
    design_assistant = {
        "id": f"designer-{project_id}",
        "assistant_type": "bom-generator",
        "purpose": f"Generated BOM for {target_platform} {variant} design",
        "checks": [
            {"check_name": "power-budget", "category": "power", "severity": "high"},
            {"check_name": "pin-conflicts", "category": "routing", "severity": "high"},
            {"check_name": "thermal-analysis", "category": "thermal", "severity": "medium"},
        ],
        "recommendations": [
            {
                "recommendation": "Add bypass capacitors within 5mm of power pins",
                "rationale": "Improve power supply stability and reduce EMI",
            },
            {
                "recommendation": "Route high-speed traces away from antenna",
                "rationale": "Minimize RF interference",
            },
        ],
    }

    # Create hardware project output
    hardware_project = {
        "id": project_id,
        "name": request_data.get("name", f"Hardware Design - {project_id}"),
        "description": request_data.get("description", "Hardware design baseline"),
        "target_platform": target_platform,
        "version": "1.0.0",
        "design_stage": "schematic",
    }

    return {
        "project_id": project_id,
        "hardware_project": hardware_project,
        "bom": bom,
        "design_assistant": design_assistant,
        "generated_at": datetime.now().isoformat(),
    }


def main():
    """Main entry point."""
    # Create sample request
    request = {
        "project_id": "hw-esp32-iot-gateway-v1",
        "name": "IoT Gateway with ESP32",
        "description": "WiFi/BLE gateway for sensor networks",
        "target_platform": "esp32",
        "variant": "esp32-s3",
    }

    # Process request
    result = process_hardware_request(request)

    # Output result
    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    main()
