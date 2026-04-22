#!/usr/bin/env python3
"""Integration tests for the full chain."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

from hardware_design_processor import process_hardware_request
from procurement_evaluator import evaluate_bom
from edition_resolver import resolve_editions
from site_generator import generate_site


def test_hardware_to_procurement_flow():
    """Test hardware design to procurement flow."""
    # Step 1: Hardware design
    hardware_request = {
        "project_id": "hw-integration-test-v1",
        "name": "Integration Test Hardware",
        "description": "Test hardware design",
        "target_platform": "esp32",
        "variant": "esp32-s3",
    }

    hardware_result = process_hardware_request(hardware_request)

    # Step 2: Procurement evaluation
    procurement_result = evaluate_bom(hardware_result["bom"])

    # Verify data flow
    assert hardware_result["project_id"] == procurement_result["project_id"]
    assert len(procurement_result["product_records"]) == len(hardware_result["bom"]["components"])

    print("✓ test_hardware_to_procurement_flow passed")


def test_procurement_to_edition_flow():
    """Test procurement to edition resolution flow."""
    hardware_request = {
        "project_id": "hw-integration-test-v2",
        "target_platform": "esp32",
    }

    hardware_result = process_hardware_request(hardware_request)
    procurement_result = evaluate_bom(hardware_result["bom"])

    # Step 3: Edition resolution
    edition_result = resolve_editions(hardware_result, procurement_result)

    # Verify data flow
    assert hardware_result["project_id"] == edition_result["project_id"]
    assert len(edition_result["editions"]) > 0

    # Verify procurement data was used in packaging
    for edition_data in edition_result["editions"]:
        packaging = edition_data["packaging"]
        assert len(packaging["bundle_contents"]) > 0

    print("✓ test_procurement_to_edition_flow passed")


def test_edition_to_website_flow():
    """Test edition to website generation flow."""
    hardware_request = {
        "project_id": "hw-integration-test-v3",
        "target_platform": "esp32",
    }

    hardware_result = process_hardware_request(hardware_request)
    procurement_result = evaluate_bom(hardware_result["bom"])
    edition_result = resolve_editions(hardware_result, procurement_result)

    # Step 4: Website generation
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        site_result = generate_site(edition_result, tmpdir)

        # Verify data flow
        assert len(site_result["generated_pages"]) > 0
        assert Path(site_result["sitemap"]).exists()

    print("✓ test_edition_to_website_flow passed")


def test_full_integration_chain():
    """Test complete integration chain end-to-end."""
    hardware_request = {
        "project_id": "hw-full-integration-test-v1",
        "name": "Full Integration Test",
        "description": "Complete end-to-end test",
        "target_platform": "esp32",
        "variant": "esp32-s3",
    }

    # Execute full chain
    hardware = process_hardware_request(hardware_request)
    procurement = evaluate_bom(hardware["bom"])
    editions = resolve_editions(hardware, procurement)

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        website = generate_site(editions, tmpdir)

        # Verify all stages completed
        assert hardware is not None
        assert procurement is not None
        assert editions is not None
        assert website is not None

        # Verify data integrity through chain
        assert hardware["project_id"] == procurement["project_id"]
        assert procurement["project_id"] == editions["project_id"]
        assert website["generated_pages"] is not None

        # Verify key artifacts exist
        assert len(hardware["bom"]["components"]) > 0
        assert len(procurement["procurement_decisions"]) > 0
        assert len(editions["editions"]) > 0
        assert len(website["generated_pages"]) > 0

    print("✓ test_full_integration_chain passed")


def test_cost_tracking_through_chain():
    """Test that costs are properly tracked through chain."""
    hardware_request = {
        "project_id": "hw-cost-test-v1",
        "target_platform": "esp32",
    }

    hardware = process_hardware_request(hardware_request)
    procurement = evaluate_bom(hardware["bom"])

    # Verify cost values
    bom_cost = hardware["bom"]["total_cost"]
    procurement_cost = procurement["summary"]["total_procurement_cost"]

    assert bom_cost > 0
    assert procurement_cost > 0
    assert isinstance(bom_cost, (int, float))
    assert isinstance(procurement_cost, (int, float))

    print("✓ test_cost_tracking_through_chain passed")


def test_error_propagation():
    """Test that errors in early stages are caught."""
    hardware_request = {
        "project_id": "hw-error-test",
        "target_platform": "unsupported",
    }

    try:
        process_hardware_request(hardware_request)
        assert False, "Should have raised ValueError"
    except ValueError:
        # Expected behavior
        pass

    print("✓ test_error_propagation passed")


def test_nordic_variant_through_chain():
    """Test Nordic variant through full chain."""
    hardware_request = {
        "project_id": "hw-nordic-chain-test-v1",
        "target_platform": "nrf52840",
        "variant": "nrf52840",
    }

    hardware = process_hardware_request(hardware_request)
    procurement = evaluate_bom(hardware["bom"])
    editions = resolve_editions(hardware, procurement)

    # Verify Nordic-specific behavior
    assert hardware["hardware_project"]["target_platform"] == "nrf52840"
    assert len(procurement["procurement_decisions"]) > 0

    print("✓ test_nordic_variant_through_chain passed")


if __name__ == "__main__":
    test_hardware_to_procurement_flow()
    test_procurement_to_edition_flow()
    test_edition_to_website_flow()
    test_full_integration_chain()
    test_cost_tracking_through_chain()
    test_error_propagation()
    test_nordic_variant_through_chain()

    print("\n✅ All integration tests passed!")
