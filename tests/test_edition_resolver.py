#!/usr/bin/env python3
"""Tests for edition resolver."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

from edition_resolver import resolve_editions, create_edition, create_packaging


def test_edition_creation():
    """Test edition creation."""
    edition = create_edition(
        edition_id="edition-test-macos-v1",
        name="Test Edition",
        platform="macos",
        features=["core-device-control", "api-access"],
        hardware_specs={"target_platform": "esp32"},
    )

    assert edition["id"] == "edition-test-macos-v1"
    assert edition["name"] == "Test Edition"
    assert edition["target_platform"] == "macos"
    assert len(edition["feature_set"]) == 2
    assert "core-device-control" in edition["feature_set"]

    print("✓ test_edition_creation passed")


def test_packaging_creation():
    """Test packaging creation."""
    packaging = create_packaging(
        edition_id="edition-test-macos-v1",
        bundle_contents=[
            {"product_id": "prod-001", "quantity": 1, "role": "hardware"}
        ],
        platform="macos",
    )

    assert packaging["edition_id"] == "edition-test-macos-v1"
    assert "pkg" in packaging["id"]
    assert len(packaging["deployment_instructions"]) > 0
    assert len(packaging["prerequisites"]) > 0
    assert len(packaging["post_deployment_setup"]) > 0

    print("✓ test_packaging_creation passed")


def test_edition_resolution():
    """Test full edition resolution."""
    hardware_data = {
        "project_id": "hw-esp32-test-v1",
        "hardware_project": {
            "id": "hw-esp32-test-v1",
            "name": "Test ESP32 Project",
            "target_platform": "esp32",
        },
    }

    procurement_data = {
        "project_id": "hw-esp32-test-v1",
        "procurement_decisions": [
            {
                "product_id": "prod-001",
                "quantity": 1,
                "score": 85.0,
            },
            {
                "product_id": "prod-002",
                "quantity": 2,
                "score": 80.0,
            },
        ],
    }

    result = resolve_editions(hardware_data, procurement_data)

    assert result["project_id"] == "hw-esp32-test-v1"
    assert "editions" in result
    assert "feature_definitions" in result

    # Verify editions
    editions = result["editions"]
    assert len(editions) == 3  # macos, windows, web

    platforms = [e["edition"]["target_platform"] for e in editions]
    assert "macos" in platforms
    assert "windows" in platforms
    assert "web" in platforms

    print("✓ test_edition_resolution passed")


def test_edition_structure():
    """Test edition object structure."""
    hardware_data = {
        "project_id": "hw-test",
        "hardware_project": {"target_platform": "esp32"},
    }

    procurement_data = {
        "project_id": "hw-test",
        "procurement_decisions": [{"product_id": "prod-001", "quantity": 1, "score": 85.0}],
    }

    result = resolve_editions(hardware_data, procurement_data)

    for edition_data in result["editions"]:
        edition = edition_data["edition"]
        packaging = edition_data["packaging"]

        # Verify edition structure
        assert "id" in edition
        assert "name" in edition
        assert "target_platform" in edition
        assert "feature_set" in edition
        assert isinstance(edition["feature_set"], list)

        # Verify packaging structure
        assert "id" in packaging
        assert "edition_id" in packaging
        assert "bundle_contents" in packaging
        assert "deployment_instructions" in packaging

    print("✓ test_edition_structure passed")


def test_feature_definitions():
    """Test that feature definitions are created."""
    hardware_data = {
        "project_id": "hw-test",
        "hardware_project": {"target_platform": "esp32"},
    }

    procurement_data = {
        "project_id": "hw-test",
        "procurement_decisions": [{"product_id": "prod-001", "quantity": 1, "score": 85.0}],
    }

    result = resolve_editions(hardware_data, procurement_data)
    features = result["feature_definitions"]

    # Check for expected features
    assert "core-device-control" in features
    assert "advanced-analytics" in features
    assert "api-access" in features

    # Verify feature structure
    for feature_id, feature_def in features.items():
        assert "id" in feature_def
        assert "name" in feature_def
        assert "category" in feature_def
        assert "description" in feature_def
        assert "platform_support" in feature_def

    print("✓ test_feature_definitions passed")


def test_platform_specific_features():
    """Test that platforms get different feature sets."""
    hardware_data = {
        "project_id": "hw-test",
        "hardware_project": {"target_platform": "esp32"},
    }

    procurement_data = {
        "project_id": "hw-test",
        "procurement_decisions": [{"product_id": "prod-001", "quantity": 1, "score": 85.0}],
    }

    result = resolve_editions(hardware_data, procurement_data)

    editions_by_platform = {e["edition"]["target_platform"]: e["edition"] for e in result["editions"]}

    # Web should have fewer features than macos
    web_features = editions_by_platform["web"]["feature_set"]
    macos_features = editions_by_platform["macos"]["feature_set"]

    assert len(web_features) < len(macos_features)

    # Verify feature constraints
    assert "api-access" in macos_features
    assert "api-access" not in web_features

    print("✓ test_platform_specific_features passed")


if __name__ == "__main__":
    test_edition_creation()
    test_packaging_creation()
    test_edition_resolution()
    test_edition_structure()
    test_feature_definitions()
    test_platform_specific_features()

    print("\n✅ All edition resolver tests passed!")
