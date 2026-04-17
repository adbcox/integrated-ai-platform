from framework.runtime_manifest_builder import build_runtime_manifest

def generate_manifest_validation_report():
    manifest = build_runtime_manifest()

    categories_sum = sum(manifest["categories"].values())
    expected_categories = {"session_contracts", "execution_contracts", "validation_contracts", "artifact_contracts", "routing_contracts"}
    actual_categories = set(manifest["categories"].keys())

    manifest_valid = (
        manifest["total_schema_entries"] == 99 and
        manifest["categories_defined"] == 5 and
        categories_sum == 99 and
        actual_categories == expected_categories and
        manifest["manifest_complete"] is True
    )

    return {
        "manifest_version": manifest["manifest_version"],
        "total_entries": manifest["total_schema_entries"],
        "category_count": manifest["categories_defined"],
        "category_coverage": categories_sum,
        "modules_present": len(manifest["modules_present"]),
        "prefixes_present": len(manifest["prefix_distribution"]),
        "manifest_valid": manifest_valid,
    }
