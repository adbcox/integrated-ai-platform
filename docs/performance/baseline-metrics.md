# Performance Baseline Metrics

**Measurement Date:** April 27, 2026
**Phase:** 10 (Validation Complete)
**Configuration:** 10 MCP servers operational

## Response Time Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Average Response Time | ~12ms | <500ms | ✅ Excellent |
| P50 (Median) | ~10ms | <300ms | ✅ |
| P95 | ~25ms | <800ms | ✅ |
| P99 | ~35ms | <1000ms | ✅ |

*Measured at Obot API layer; excludes phat container cold-start time.*

## Resource Usage (Obot container)

| Resource | Current | Peak | Limit | Status |
|----------|---------|------|-------|--------|
| CPU Usage | ~4.3% | ~8.5% | 50% | ✅ |
| RAM Usage | ~334 MB | ~512 MB | 2 GB | ✅ |
| Disk I/O | Minimal | Low | N/A | ✅ |

## Per-Server Metrics

| Server | Runtime | Tools | First-Call Latency | Steady-State |
|--------|---------|-------|--------------------|--------------|
| Filesystem | remote | 14 | Instant | ~5ms |
| Docker | remote | 19 | Instant | ~6ms |
| Docs | remote | 10 | Instant | ~7ms |
| PostgreSQL | npx phat | 1 | ~18s cold start | ~8ms |
| GitHub | npx phat | 26 | ~28s cold start | ~18ms |
| Weather | npx phat | 17 | ~25s cold start | ~15ms |
| Health & Fitness | npx phat | 17 | ~22s cold start | ~12ms |
| Semgrep | npx phat | 7 | ~24s cold start | ~14ms |
| Strava | npx phat | 24 | ~26s cold start | ~16ms |
| Home Assistant | npx phat | 3 | ~20s cold start | ~10ms |

## Error Rates (Phase 10 validation)

| Error Type | Count | Rate | Target | Status |
|------------|-------|------|--------|--------|
| Total Errors | 0 | 0% | <1% | ✅ |
| Timeout | 0 | 0% | <0.5% | ✅ |
| Auth Failure | 0 | 0% | <0.1% | ✅ |
| Server 503 | 0 | 0% | <0.5% | ✅ |

## Known Bottlenecks

| Bottleneck | Impact | Mitigation |
|------------|--------|------------|
| Phat container cold start (20-30s) | First call per session slow | Pre-warm by calling tools once after Obot restart |
| Strava token expiry (~6h) | Auth failures when token expires | Manual refresh until automation implemented |
| GitHub rate limit (5000/hour) | Failures on heavy usage | Monitor via `/rate_limit` endpoint |
| Docs server startup (~3min) | Long container start on rebuild | Only rebuilt on `force-recreate` |

## Capacity Planning

**Current load:** 10 servers, 138 tools, ~100 tool calls/hour estimated

**Headroom:**
- ~50 servers max before resource saturation
- ~500 tools before context window pressure on AI clients
- ~1000 tool calls/hour sustainable on current hardware

## Monitoring Recommendations

Alert thresholds to configure in Grafana/Uptime Kuma:
- Response time >1000ms (sustained 5 min)
- Error rate >1%
- CPU >50%
- RAM >4GB
- Any remote HTTP endpoint failing healthcheck

Review quarterly:
- Capacity vs actual usage
- Stale/unused servers to deregister
- Package version updates
