from typing import Any

def run_integration_harness(contract_manifest: Any, seal_registry: Any, harness_config: Any) -> dict[str, Any]:
    if not isinstance(contract_manifest, dict) or not isinstance(seal_registry, dict) or not isinstance(harness_config, dict):
        return {"harness_status": "invalid_input"}
    c_ok = contract_manifest.get("contract_status") == "built"
    r_ok = seal_registry.get("registry_status") == "built"
    if not c_ok or not r_ok:
        return {"harness_status": "invalid_input"}
    try:
        from framework.live_bridge_handshake_completer import complete_handshake
        from framework.live_bridge_cycle_completion_reporter import report_cycle_completion
        from framework.live_bridge_federation_handshake_sealer import seal_federation_handshake
    except ImportError as e:
        return {"harness_status": "import_failed", "missing": str(e)}
    success_chain_count = 0
    gate_assert_count = 0
    final_seal = None
    handshake = complete_handshake(
        {"operator_attachment_status": "attached"},
        {"phase6_entry_report_status": "complete"},
        {"external_manifest_status": "built"},
    )
    if handshake.get("handshake_status") == "completed":
        success_chain_count += 1
    else:
        return {"harness_status": "failed", "failed_at": "handshake_completer", "observed_status": handshake.get("handshake_status")}
    cycle_completion = report_cycle_completion(
        {"cycle_finalization_status": "finalized"},
        {"cycle_summary_status": "complete"},
        "p1",
    )
    if cycle_completion.get("cycle_completion_report_status") == "complete":
        success_chain_count += 1
    else:
        return {"harness_status": "failed", "failed_at": "cycle_completion_reporter", "observed_status": cycle_completion.get("cycle_completion_report_status")}
    federation_seal = seal_federation_handshake(
        {"fed_completion_report_status": "complete"},
        {"fed_peer_rollup_status": "rolled_up"},
        {},
    )
    if federation_seal.get("fed_seal_status") == "sealed":
        success_chain_count += 1
        final_seal = "sealed"
    else:
        return {"harness_status": "failed", "failed_at": "federation_sealer", "observed_status": federation_seal.get("fed_seal_status")}
    handshake_bad = complete_handshake({}, {}, {})
    if handshake_bad.get("handshake_status") != "completed":
        gate_assert_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_gate": "handshake_status"}
    cycle_bad = report_cycle_completion({}, {"cycle_summary_status": "complete"}, "p1")
    if cycle_bad.get("cycle_completion_report_status") != "complete":
        gate_assert_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_gate": "cycle_completion_report_status"}
    seal_bad = seal_federation_handshake({}, {"fed_peer_rollup_status": "rolled_up"}, {})
    if seal_bad.get("fed_seal_status") != "sealed":
        gate_assert_count += 1
    else:
        return {"harness_status": "gate_failed", "failed_gate": "fed_seal_status"}
    if success_chain_count > 0 and gate_assert_count == 3 and final_seal == "sealed":
        return {
            "harness_status": "passed",
            "success_chain_length": success_chain_count,
            "gate_assertions_passed": gate_assert_count,
            "terminal_seal_value": final_seal,
        }
    return {"harness_status": "failed", "reason": "gate_conditions_not_met"}

