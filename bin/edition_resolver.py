#!/usr/bin/env python3
"""Edition resolver: creates platform-specific editions from hardware and features."""

import json
from datetime import datetime


def create_edition(
    edition_id: str,
    name: str,
    platform: str,
    features: list,
    hardware_specs: dict,
) -> dict:
    """Create an edition definition."""
    return {
        "id": edition_id,
        "name": name,
        "description": f"{name} - {platform.title()} Edition",
        "feature_set": features,
        "target_platform": platform,
        "version": "1.0.0",
    }


def create_packaging(
    edition_id: str,
    bundle_contents: list,
    platform: str,
) -> dict:
    """Create packaging definition."""
    if platform == "macos":
        deployment_instructions = [
            "1. Extract app-bundle.zip",
            "2. Right-click app and select 'Open' (security approval)",
            "3. Follow onboarding wizard",
            "4. Start using the control center",
        ]
    elif platform == "windows":
        deployment_instructions = [
            "1. Run installer.msi",
            "2. Accept security prompts",
            "3. Complete installation",
            "4. Launch from Start Menu",
        ]
    else:
        deployment_instructions = [
            "1. Follow platform-specific deployment steps",
            "2. Configure prerequisites",
            "3. Deploy application",
        ]

    return {
        "id": f"pkg-{edition_id}-{platform}",
        "edition_id": edition_id,
        "bundle_contents": bundle_contents,
        "deployment_instructions": deployment_instructions,
        "prerequisites": [
            "System with minimum 2GB RAM",
            "Network connectivity (WiFi/Ethernet)",
            "Modern browser (Chrome, Safari, Firefox, Edge)",
        ],
        "post_deployment_setup": [
            "Configure network settings",
            "Link hardware devices",
            "Enable analytics (optional)",
            "Set preferences",
        ],
    }


def resolve_editions(hardware_data: dict, procurement_data: dict) -> dict:
    """Resolve editions based on hardware and procurement."""
    project_id = hardware_data.get("project_id")

    # Define feature sets for different editions
    base_features = [
        "core-device-control",
        "basic-monitoring",
        "device-dashboard",
    ]

    pro_features = base_features + [
        "advanced-analytics",
        "multi-device-management",
        "api-access",
        "custom-workflows",
    ]

    enterprise_features = pro_features + [
        "advanced-security",
        "team-management",
        "audit-logs",
        "priority-support",
    ]

    # Get selected products from procurement
    selected_products = procurement_data.get("procurement_decisions", [])[:3]
    product_bundle = [
        {
            "product_id": p["product_id"],
            "quantity": p["quantity"],
            "role": "hardware-component",
        }
        for p in selected_products
    ]

    # Create editions for each platform
    editions = []
    platforms = ["macos", "windows", "web"]

    for platform in platforms:
        # Select appropriate features
        if platform == "web":
            features = base_features
            name = f"Community Edition"
        elif platform == "windows":
            features = pro_features
            name = f"Professional Edition"
        else:  # macos
            features = enterprise_features
            name = f"Enterprise Edition"

        edition_id = f"edition-{project_id.replace('hw-', '')}-{platform}-v1"

        edition = create_edition(
            edition_id=edition_id,
            name=name,
            platform=platform,
            features=features,
            hardware_specs=hardware_data.get("hardware_project", {}),
        )

        packaging = create_packaging(
            edition_id=edition_id,
            bundle_contents=product_bundle,
            platform=platform,
        )

        editions.append({
            "edition": edition,
            "packaging": packaging,
        })

    return {
        "project_id": project_id,
        "editions": editions,
        "feature_definitions": {
            "core-device-control": {
                "id": "core-device-control",
                "name": "Device Control",
                "category": "core",
                "description": "Basic control of connected devices",
                "dependencies": [],
                "platform_support": {
                    "macos": {"supported": True, "minimum_version": "10.15"},
                    "windows": {"supported": True, "minimum_version": "10"},
                    "web": {"supported": True},
                },
            },
            "advanced-analytics": {
                "id": "advanced-analytics",
                "name": "Advanced Analytics",
                "category": "advanced",
                "description": "Detailed metrics and historical analysis",
                "dependencies": ["core-device-control"],
                "platform_support": {
                    "macos": {"supported": True, "minimum_version": "10.15"},
                    "windows": {"supported": True, "minimum_version": "10"},
                    "web": {"supported": False},
                },
            },
            "api-access": {
                "id": "api-access",
                "name": "API Access",
                "category": "enterprise",
                "description": "REST API for programmatic control",
                "dependencies": ["core-device-control"],
                "platform_support": {
                    "macos": {"supported": True},
                    "windows": {"supported": True},
                    "web": {"supported": False},
                },
            },
        },
        "resolved_at": datetime.now().isoformat(),
    }


def main():
    """Main entry point."""
    sample_hardware = {
        "project_id": "hw-esp32-iot-gateway-v1",
        "hardware_project": {
            "id": "hw-esp32-iot-gateway-v1",
            "name": "IoT Gateway with ESP32",
            "target_platform": "esp32",
        },
    }

    sample_procurement = {
        "project_id": "hw-esp32-iot-gateway-v1",
        "procurement_decisions": [
            {
                "product_id": "prod-esp32-s3-wroom-1-n8",
                "quantity": 1,
                "score": 85.0,
            },
            {
                "product_id": "prod-ams1117-3v3",
                "quantity": 1,
                "score": 82.0,
            },
        ],
    }

    result = resolve_editions(sample_hardware, sample_procurement)
    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    main()
