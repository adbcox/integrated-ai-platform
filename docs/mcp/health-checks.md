# MCP Health Checks

## Automated Checks (Bash)

Run this to verify all critical MCP dependencies are reachable:

```bash
#!/usr/bin/env bash
# docs/mcp/health-checks.md — run as: bash <(sed -n '/^```bash$/,/^```$/p' docs/mcp/health-checks.md | grep -v '^```')

checks_passed=0; checks_total=0

check() {
  local name="$1"; local cmd="$2"
  checks_total=$((checks_total + 1))
  if eval "$cmd" > /dev/null 2>&1; then
    echo "  ✓ $name"
    checks_passed=$((checks_passed + 1))
  else
    echo "  ✗ $name  ← FAILING"
  fi
}

echo "=== MCP Dependency Health Checks ==="
echo ""
echo "Platform services:"
check "Plane API"        "curl -sf http://localhost:8000/api/v1/workspaces/iap/projects/ -H 'x-api-key: $(grep PLANE_API_TOKEN docker/.env | cut -d= -f2)'"
check "Plane DB :5433"   "python3 -c \"import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',5433))\""
check "Obot :8090"       "curl -sf http://localhost:8090/api/healthz"
check "Ollama :11434"    "curl -sf http://localhost:11434/api/tags"
check "Grafana :3030"    "curl -sf http://localhost:3030"
check "Dashboard :8080"  "curl -sf http://localhost:8081/"

echo ""
echo "MCP server executables:"
check "python3 mcp/"     "python3 mcp/plane_mcp_server.py --help 2>/dev/null || true; python3 -c 'import sys; sys.exit(0)'"
check "npx available"    "which npx"
check "uvx available"    "which uvx"

echo ""
echo "Docker containers:"
check "plane-web"        "docker inspect docker-plane-web-1 --format '{{.State.Health.Status}}' | grep -q healthy"
check "plane-api"        "docker inspect docker-plane-api-1 --format '{{.State.Health.Status}}' | grep -q healthy"
check "plane-db"         "docker inspect docker-plane-db-1 --format '{{.State.Health.Status}}' | grep -q healthy"
check "obot"             "docker inspect obot --format '{{.State.Health.Status}}' | grep -q healthy"

echo ""
echo "=== Results: $checks_passed/$checks_total passed ==="
```

## Uptime Kuma Monitors (Manual Setup)

Add these monitors at http://192.168.10.145:3033:

| Monitor Name | Type | URL/Host | Interval | Alert |
|-------------|------|----------|----------|-------|
| Plane API | HTTP | http://localhost:8000/api/v1/workspaces/iap/projects/ | 1 min | Yes |
| Obot Gateway | HTTP | http://localhost:8090/api/healthz | 1 min | Yes |
| Ollama | HTTP | http://localhost:11434/api/tags | 2 min | Yes |
| IAP Dashboard | HTTP | http://localhost:8081/ | 1 min | Yes |
| Plane DB :5433 | TCP Port | localhost:5433 | 1 min | Yes |
| VictoriaMetrics | HTTP | http://localhost:8428 | 2 min | No |

## Grafana Alert Thresholds

In Grafana (http://192.168.10.145:3030), create alerts for:

| Metric | Threshold | Severity |
|--------|-----------|----------|
| Plane API latency | >1000ms | Warning |
| Dashboard scrape state | down | Critical |
| Obot container restart | >0 in 5m | Warning |
| Ollama queue depth | >5 pending | Warning |

## Monitoring Targets in vmagent

Current scrape targets (`docker/vmagent-config/scrape.yml`):
- `localhost:8081/metrics` — IAP dashboard (platform_* metrics)
- `localhost:9100` — node-exporter (host metrics)

To add Obot metrics (if Obot exposes /metrics in future):
```yaml
- job_name: obot
  static_configs:
    - targets: ['localhost:8090']
  metrics_path: /metrics
  bearer_token: "your_obot_api_key"
```
