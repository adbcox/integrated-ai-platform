from typing import Any

def run_integration_harness(contract_manifest, seal_registry, harness_config):
    if not isinstance(contract_manifest, dict) or not isinstance(seal_registry, dict) or not isinstance(harness_config, dict):
        return {"harness_status": "invalid_input"}
    if contract_manifest.get("shape_contract_manifest_status") != "published" or seal_registry.get("seal_token_registry_status") != "published":
        return {"harness_status": "invalid_input"}
    try:
        from framework.live_bridge_fed_governance_control_plane import build_fed_governance_control_plane
        from framework.live_bridge_adapter_governance_binder import bind_adapter_governance
        from framework.live_bridge_adapter_layer_sealer import seal_adapter_layer
        from framework.live_bridge_tap_registrar import register_tap
        from framework.live_bridge_governed_federation_sealer import seal_governed_federation
        from framework.live_bridge_obs_layer_sealer import seal_obs_layer
    except ImportError as e:
        return {"harness_status": "import_failed", "missing": str(e)}
    success_chain_count = 0
    gate_assert_count = 0
    final_seal = None
    fed_gov_cp = build_fed_governance_control_plane(
        {"fed_gov_validation_status": "valid", "validated_fed_gov_env_id": "env-int2"},
        {"fed_gov_rollup_status": "rolled_up"},
        {"message_count": 1},
    )
    if fed_gov_cp.get("fed_gov_cp_status") == "operational":
        success_chain_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_at": "fed_gov_cp"}
    adapter_binding = bind_adapter_governance(
        {"adapter_scope_binding_status": "bound", "adapter_id": "adp-int2"},
        fed_gov_cp,
        {},
    )
    if adapter_binding.get("adapter_governance_binding_status") == "bound":
        success_chain_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_at": "adapter_binding"}
    adapter_seal = seal_adapter_layer(
        {"adapter_layer_gate_status": "open"},
        {"adapter_cp_status": "operational", "adapter_cp_env_id": "env-int2"},
        {},
    )
    if adapter_seal.get("adapter_layer_seal_status") == "sealed":
        success_chain_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_at": "adapter_seal"}
    tap_result = register_tap(
        {"tap_descriptor_status": "described", "tap_id": "tap-int2", "tap_kind": "metric"},
        adapter_seal,
    )
    if tap_result.get("tap_registration_status") == "registered":
        success_chain_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_at": "tap_result"}
    gov_fed_seal = seal_governed_federation(
        {"governed_fed_completion_report_status": "complete", "report_phase": "p6"},
        {"fed_gov_rollup_status": "rolled_up"},
        {"seal_id": "gfseal-int2"},
    )
    if gov_fed_seal.get("governed_fed_seal_status") == "sealed":
        success_chain_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_at": "gov_fed_seal"}
    obs_seal = seal_obs_layer(
        {"obs_layer_finalization_status": "finalized"},
        {"obs_layer_report_status": "reported"},
    )
    if obs_seal.get("obs_layer_seal_status") == "sealed":
        success_chain_count += 1
        final_seal = "sealed"
    else:
        return {"harness_status": "gate_failed", "failed_at": "obs_seal"}
    fed_gov_cp_bad = build_fed_governance_control_plane({}, {}, {"message_count": 0})
    if fed_gov_cp_bad.get("fed_gov_cp_status") != "operational":
        gate_assert_count += 1
    gov_binding_bad = bind_adapter_governance({"adapter_scope_binding_status": "bound"}, {}, {})
    if gov_binding_bad.get("adapter_governance_binding_status") != "bound":
        gate_assert_count += 1
    adapter_seal_bad = seal_adapter_layer({}, {"adapter_cp_status": "operational"}, {})
    if adapter_seal_bad.get("adapter_layer_seal_status") != "sealed":
        gate_assert_count += 1
    tap_bad = register_tap({"tap_descriptor_status": "described"}, {})
    if tap_bad.get("tap_registration_status") != "registered":
        gate_assert_count += 1
    gov_fed_seal_bad = seal_governed_federation({}, {"fed_gov_rollup_status": "rolled_up"}, {})
    if gov_fed_seal_bad.get("governed_fed_seal_status") != "sealed":
        gate_assert_count += 1
    obs_seal_bad = seal_obs_layer({}, {})
    if obs_seal_bad.get("obs_layer_seal_status") != "sealed":
        gate_assert_count += 1
    if success_chain_count == 6 and gate_assert_count == 6 and final_seal == "sealed":
        return {
            "harness_status": "passed",
            "success_chain_length": 6,
            "gate_assertions_passed": 6,
            "terminal_seal_value": "sealed",
        }
    return {"harness_status": "gate_failed", "success_chain_count": success_chain_count, "gate_assert_count": gate_assert_count}
