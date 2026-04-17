from typing import Any

def get_shape_contract_manifest() -> dict[str, Any]:
    contracts = {
        "LOB-W1": [
            {
                "producer_module": "framework.live_bridge_bridge_control_plane",
                "producer_function": "build_bridge_control_plane",
                "producer_key": "bridge_cp_status",
                "producer_success_value": "operational",
                "consumer_module": "framework.live_bridge_cycle_tick_scheduler",
                "consumer_function": "schedule_tick",
                "consumer_reads_key": "bridge_cp_status",
                "consumer_required_value": "operational",
            },
            {
                "producer_module": "framework.live_bridge_bridge_health_monitor",
                "producer_function": "monitor_bridge_health",
                "producer_key": "bridge_health_status",
                "producer_success_value": "healthy",
                "consumer_module": "framework.live_bridge_cycle_health_watch",
                "consumer_function": "watch_cycle_health",
                "consumer_reads_key": "bridge_health_status",
                "consumer_required_value": "healthy",
            },
        ],
        "LOB-W2": [
            {
                "producer_module": "framework.live_bridge_cycle_completion_reporter",
                "producer_function": "report_cycle_completion",
                "producer_key": "cycle_completion_report_status",
                "producer_success_value": "complete",
                "consumer_module": "framework.live_bridge_federation_membership_registrar",
                "consumer_function": "register_federation_membership",
                "consumer_reads_key": "cycle_completion_report_status",
                "consumer_required_value": "complete",
            },
            {
                "producer_module": "framework.live_bridge_cycle_control_plane",
                "producer_function": "build_cycle_control_plane",
                "producer_key": "cycle_cp_status",
                "producer_success_value": "operational",
                "consumer_module": "framework.live_bridge_federation_validator",
                "consumer_function": "validate_federation",
                "consumer_reads_key": "cycle_cp_status",
                "consumer_required_value": "operational",
            },
            {
                "producer_module": "framework.live_bridge_cycle_health_watch",
                "producer_function": "watch_cycle_health",
                "producer_key": "cycle_health_watch_status",
                "producer_success_value": "green",
                "consumer_module": "framework.live_bridge_federation_health_watch",
                "consumer_function": "watch_federation_health",
                "consumer_reads_key": "cycle_health_watch_status",
                "consumer_required_value": "green",
            },
            {
                "producer_module": "framework.live_bridge_cycle_quota_tracker",
                "producer_function": "track_quota",
                "producer_key": "quota_tracker_status",
                "producer_success_value": "under_limit",
                "consumer_module": "framework.live_bridge_federation_quota_aggregator",
                "consumer_function": "aggregate_quota",
                "consumer_reads_key": "quota_tracker_status",
                "consumer_required_value": "under_limit",
            },
            {
                "producer_module": "framework.live_bridge_operation_acknowledger",
                "producer_function": "acknowledge_operation",
                "producer_key": "acknowledgement_status",
                "producer_success_value": "acknowledged",
                "consumer_module": "framework.live_bridge_federation_receipt_aggregator",
                "consumer_function": "aggregate_receipts",
                "consumer_reads_key": "acknowledgement_status",
                "consumer_required_value": "acknowledged",
            },
        ],
        "LOB-W3": [
            {
                "producer_module": "framework.live_bridge_handshake_completer",
                "producer_function": "complete_handshake",
                "producer_key": "handshake_status",
                "producer_success_value": "completed",
                "consumer_module": "framework.live_bridge_federation_membership_registrar",
                "consumer_function": "register_federation_membership",
                "consumer_reads_key": "handshake_status",
                "consumer_required_value": "completed",
            },
            {
                "producer_module": "framework.live_bridge_federation_handshake_sealer",
                "producer_function": "seal_federation_handshake",
                "producer_key": "fed_seal_status",
                "producer_success_value": "sealed",
                "consumer_module": "TERMINAL",
                "consumer_function": "TERMINAL",
                "consumer_reads_key": "fed_seal_status",
                "consumer_required_value": "sealed",
            },
        ],
    }
    all_valid = True
    total_pairs = 0
    for package_key, entries in contracts.items():
        if not isinstance(entries, list) or len(entries) == 0:
            all_valid = False
            break
        for entry in entries:
            if not isinstance(entry, dict):
                all_valid = False
                break
            required_keys = {
                "producer_module",
                "producer_function",
                "producer_key",
                "producer_success_value",
                "consumer_module",
                "consumer_function",
                "consumer_reads_key",
                "consumer_required_value",
            }
            if set(entry.keys()) != required_keys:
                all_valid = False
                break
            for k, v in entry.items():
                if not isinstance(v, str) or len(v) == 0:
                    all_valid = False
                    break
            if not all_valid:
                break
            total_pairs += 1
        if not all_valid:
            break
    if all_valid and total_pairs >= 9:
        return {"contract_status": "built", "contract_pair_count": total_pairs}
    return {"contract_status": "invalid", "contract_pair_count": 0}

