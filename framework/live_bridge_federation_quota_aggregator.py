from typing import Any

def aggregate_quota(local_quota: dict[str, Any], peer_quota_report: dict[str, Any], aggregator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(local_quota, dict) or not isinstance(peer_quota_report, dict) or not isinstance(aggregator_config, dict):
        return {"fed_quota_status": "invalid_input"}
    local_used = local_quota.get("used", 0)
    peer_used = peer_quota_report.get("peer_used", 0)
    total_used = local_used + peer_used
    fed_quota = aggregator_config.get("fed_quota", 1000)
    if total_used >= fed_quota:
        return {"fed_quota_status": "exceeded"}
    return {"fed_quota_status": "under_fed_limit"}

