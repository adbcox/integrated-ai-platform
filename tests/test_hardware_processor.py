#!/usr/bin/env python3
"""Tests for hardware design processor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

from hardware_design_processor import (
    process_hardware_request,
    create_bom_for_esp32,
    create_bom_for_nordic,
)


def test_esp32_bom_generation():
    """Test ESP32 BOM generation."""
    bom = create_bom_for_esp32("hw-test-esp32", "esp32-s3")

    assert bom["project_id"] == "hw-test-esp32"
    assert len(bom["components"]) > 0
    assert bom["total_cost"] > 0
    assert "sourcing_notes" in bom

    # Verify required components
    part_numbers = [c["part_number"] for c in bom["components"]]
    assert "ESP32-S3-WROOM-1-N8" in part_numbers
    assert "AMS1117-3V3" in part_numbers

    print("✓ test_esp32_bom_generation passed")


def test_nordic_bom_generation():
    """Test Nordic BOM generation."""
    bom = create_bom_for_nordic("hw-test-nordic", "nrf52840")

    assert bom["project_id"] == "hw-test-nordic"
    assert len(bom["components"]) > 0
    assert bom["total_cost"] > 0

    part_numbers = [c["part_number"] for c in bom["components"]]
    assert "NORDIC-nrf52840" in part_numbers

    print("✓ test_nordic_bom_generation passed")


def test_hardware_request_processing_esp32():
    """Test full ESP32 hardware request processing."""
    request = {
        "project_id": "hw-esp32-iot-gateway-v1",
        "name": "IoT Gateway with ESP32",
        "description": "WiFi/BLE gateway for sensor networks",
        "target_platform": "esp32",
        "variant": "esp32-s3",
    }

    result = process_hardware_request(request)

    assert result["project_id"] == "hw-esp32-iot-gateway-v1"
    assert "hardware_project" in result
    assert "bom" in result
    assert "design_assistant" in result
    assert "generated_at" in result

    # Verify hardware project
    hw = result["hardware_project"]
    assert hw["target_platform"] == "esp32"
    assert hw["design_stage"] == "schematic"

    # Verify BOM
    bom = result["bom"]
    assert bom["total_cost"] > 0
    assert len(bom["components"]) > 0

    # Verify design assistant
    da = result["design_assistant"]
    assert da["assistant_type"] == "bom-generator"
    assert len(da["checks"]) > 0
    assert len(da["recommendations"]) > 0

    print("✓ test_hardware_request_processing_esp32 passed")


def test_hardware_request_processing_nordic():
    """Test full Nordic hardware request processing."""
    request = {
        "project_id": "hw-nordic-ble-beacon-v1",
        "name": "BLE Beacon with Nordic",
        "description": "Low-power BLE beacon",
        "target_platform": "nrf52840",
        "variant": "nrf52840",
    }

    result = process_hardware_request(request)

    assert result["project_id"] == "hw-nordic-ble-beacon-v1"
    assert result["hardware_project"]["target_platform"] == "nrf52840"

    print("✓ test_hardware_request_processing_nordic passed")


def test_bom_component_structure():
    """Test that BOM components have required fields."""
    bom = create_bom_for_esp32("hw-test", "esp32-s3")

    required_fields = ["part_number", "description", "quantity", "unit_cost", "supplier", "lead_time_days"]

    for component in bom["components"]:
        for field in required_fields:
            assert field in component, f"Missing field: {field}"
            assert component[field] is not None

    print("✓ test_bom_component_structure passed")


def test_unsupported_platform():
    """Test handling of unsupported platform."""
    request = {
        "project_id": "hw-unsupported",
        "target_platform": "unsupported-platform",
    }

    try:
        process_hardware_request(request)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported platform" in str(e)
        print("✓ test_unsupported_platform passed")


def test_cost_calculation():
    """Test that total BOM cost is correctly calculated."""
    bom = create_bom_for_esp32("hw-test", "esp32-s3")

    calculated_cost = sum(c["quantity"] * c["unit_cost"] for c in bom["components"])
    assert abs(calculated_cost - bom["total_cost"]) < 0.01

    print("✓ test_cost_calculation passed")


if __name__ == "__main__":
    test_esp32_bom_generation()
    test_nordic_bom_generation()
    test_hardware_request_processing_esp32()
    test_hardware_request_processing_nordic()
    test_bom_component_structure()
    test_unsupported_platform()
    test_cost_calculation()

    print("\n✅ All hardware processor tests passed!")
