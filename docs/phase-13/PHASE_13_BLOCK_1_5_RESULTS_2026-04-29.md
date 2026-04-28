# Phase 13 Block 1.5 Closeout — 2026-04-29

Generated: 2026-04-28T06:56:56Z

Amendments applied:
1. Section 3: explicit pre-pull with --platform linux/arm64 before compose up
2. Section 4: probe /healthz output on 8091/8092/8093 before deciding to drop jobs

## 1. Vaultwarden rename verification (token → admin_token)

### Before
```
secret/vaultwarden/admin keys:
```

### Decision
```
has_token=0  has_admin_token=0
```

Action: MISSING_BOTH

### After
```
secret/vaultwarden/admin keys:
```

=== SECTION 1 COMPLETE — 26 lines ===


## 2. Seed missing Vault paths (grafana, anythingllm)

### Writes
```
* 2 errors occurred:
	* permission denied
	* invalid token



* 2 errors occurred:
	* permission denied
	* invalid token


```

### Verify
```
secret/grafana:
Error making API request.

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/grafana
Code: 403. Errors:

* 2 errors occurred:
	* permission denied
	* invalid token



secret/anythingllm:
Error making API request.

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/anythingllm
Code: 403. Errors:

* 2 errors occurred:
	* permission denied
	* invalid token



secret/grafana/api keys:

secret/anythingllm/api keys:
```

=== SECTION 2 COMPLETE — 77 lines ===


## 3. cAdvisor arm64 replacement

### Stop + remove old (amd64) cAdvisor
```
cadvisor
cadvisor
```

### Pre-pull arm64 image (amendment 1)
```
9526bc162c17: Download complete
9526bc162c17: Pull complete
Digest: sha256:3cde6faf0791ebf7b41d6f8ae7145466fed712ea6f252c935294d2608b1af388
Status: Downloaded newer image for gcr.io/cadvisor/cadvisor:v0.49.1
gcr.io/cadvisor/cadvisor:v0.49.1
```

### observability-stack.yml cadvisor block (after edit)
```yaml
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    platform: linux/arm64
    container_name: cadvisor
    restart: unless-stopped
    privileged: true
    devices:
      - /dev/kmsg
    ports:
      - "8088:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    networks:
      - observability
```

### docker compose up cadvisor
```
validating /Users/admin/repos/integrated-ai-platform/docker/observability-stack.yml: networks.cadvisor additional properties 'privileged', 'volumes', 'devices', 'image', 'networks', 'ports', 'restart', 'container_name', 'platform' not allowed
```

### Verify
```

  http://localhost:8088/healthz -> http=000

  /metrics first 20 lines:
```

### Primary failed (status=, http=000) — falling back to zcube/cadvisor
```
Error response from daemon: No such container: cadvisor
Error response from daemon: No such container: cadvisor
Digest: sha256:f5d9acd3d30db9f991b1b9dcdfe4a27c1800069fdf10f161b6f53fbf9b14ec38
Status: Downloaded newer image for zcube/cadvisor:latest
docker.io/zcube/cadvisor:latest
4137f09fad0f82ce2409eda521099ed9b3c4e97c1c4348c744b2a96d38023f56
fallback status: Up 25 seconds (health: starting)
  fallback http=200
```

=== SECTION 3 COMPLETE — 144 lines ===


## 4. Scrape config cleanup

### Probe /healthz on each MCP port (amendment 2)
```
  port 8091 /healthz:
    ok    (content-type: text/html; charset=utf-8)
  port 8092 /healthz:
    ok    (content-type: text/html; charset=utf-8)
  port 8093 /healthz:
    ok    (content-type: text/html; charset=utf-8)

### Probe Caddy /metrics
```
  http://localhost:2019/metrics:
    # HELP caddy_admin_http_requests_total Counter of requests made to the Admin API's HTTP endpoints.
    # TYPE caddy_admin_http_requests_total counter
    caddy_admin_http_requests_total{code="200",handler="admin",method="GET",path="/config/"} 632
    caddy_admin_http_requests_total{code="200",handler="admin",method="GET",path="/metrics"} 26
    caddy_admin_http_requests_total{code="200",handler="admin",method="POST",path="/load"} 2
    (content-type: text/plain; version=0.0.4; charset=utf-8; escaping=underscores)
```

### Probe node-exporter from inside vmagent
```
  via host.docker.internal:9100:
    # HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
    # TYPE go_gc_duration_seconds summary
    go_gc_duration_seconds{quantile="0"} 3.292e-06

  via 192.168.10.145:9100:
    # HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
    # TYPE go_gc_duration_seconds summary
    go_gc_duration_seconds{quantile="0"} 3.292e-06

  Is node-exporter even running on Mac mini (host)?
    COMMAND   PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    ssh     21652 admin   17u  IPv4 0x34dc796d0728594e      0t0  TCP *:9100 (LISTEN)
```

### Decisions
```
  drop mcp-filesystem (8091/healthz returns 'ok', not Prometheus)
  drop mcp-docker (8092/healthz returns 'ok', not Prometheus)
  keep mcp-docs (8093) — confirmed UP in Block 1
  keep cadvisor (8088) — fixed in §3
  keep caddy (2019/metrics) — Prometheus format confirmed
  keep node-exporter — see probe results above
```

### New scrape.yml
```yaml
global:
  scrape_interval: 30s
  scrape_timeout: 15s

scrape_configs:
  - job_name: node-exporter
    static_configs:
      - targets: ['host.docker.internal:9100']
        labels:
          host: mac-mini

  - job_name: caddy
    metrics_path: /metrics
    static_configs:
      - targets: ['host.docker.internal:2019']
        labels:
          service: caddy

  - job_name: mcp-docs
    metrics_path: /metrics
    static_configs:
      - targets: ['host.docker.internal:8093']
        labels:
          service: mcp-docs-remote

  - job_name: cadvisor
    static_configs:
      - targets: ['host.docker.internal:8088']
        labels:
          service: cadvisor

  - job_name: vmagent
    static_configs:
      - targets: ['vmagent:8429']
```
vmagent

### vmagent active targets after restart (2 scrape cycles waited)
```
[
  {
    "pool": "caddy",
    "health": "up",
    "lastError": ""
  },
  {
    "pool": "cadvisor",
    "health": "up",
    "lastError": ""
  },
  {
    "pool": "mcp-docs",
    "health": "down",
    "lastError": "unexpected status code returned when scraping \"http://host.docker.internal:8093/metrics\": 404; expecting 200; response body: \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Cannot GET /metrics</pre>\\n</body>\\n</html>\\n\""
  },
  {
    "pool": "node-exporter",
    "health": "up",
    "lastError": ""
  },
  {
    "pool": "vmagent",
    "health": "up",
    "lastError": ""
  }
]

UP target count:
4
```

=== SECTION 4 COMPLETE — 269 lines ===


## 5. Cleanup leftover Block 1 artifacts

### Before
```
./docker/vmagent-config/scrape.yml.pre-block1
./docker/vmagent-config/scrape.yml.pre-block1.5
./docker/caddy/Caddyfile.pre-block1
```
rm 'docker/caddy/Caddyfile.pre-block1'
rm 'docker/vmagent-config/scrape.yml.pre-block1'

### After
```
(empty above = clean)

.gitignore tail:
# Local databases
data/platform_analytics.db

# Phase block backup files (use git history instead)
*.pre-block*
```

=== SECTION 5 COMPLETE — 295 lines ===


## 6. Investigate Python process on :8080 (read-only)

```
PID listening on :8080: 45891
  PID  PPID USER  STARTED COMMAND
45891     1 admin Sat06PM /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python /Users/admin/repos/integrated-ai-platform/web/dashboard/server.py

Full command:
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python /Users/admin/repos/integrated-ai-platform/web/dashboard/server.py

launchctl matches:

cwd:
trustd    89381 admin  cwd       DIR               1,14      704                   2 /

Open files (top 10):
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Python3
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_asyncio.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_bisect.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_blake2.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_bz2.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_codecs_cn.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_codecs_hk.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_codecs_iso2022.cpython-39-darwin.so
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/lib-dynload/_codecs_jp.cpython-39-darwin.so

What does it serve?
  http=200 content_type=text/html

Body (first 20 lines):
  <!DOCTYPE html>
  <html lang="en">
  <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Platform — Control Plane</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <script>
  tailwind.config = { theme: { extend: { colors: {
    surface:'#0D1117', card:'#161B22', border:'#21262D', accent:'#0052CC'
  }}}}
  </script>
  <style>
    /* ── Design system variables ─────────────────────────────────────────────── */
    :root {
      /* Surfaces */
```

=== SECTION 6 COMPLETE — 351 lines ===


## 7. Final audit + commit

### 7.1 Vaultwarden keys
```
```

### 7.2 Vault paths grafana + anythingllm
```
Error making API request.

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/grafana
Code: 403. Errors:

* 2 errors occurred:
	* permission denied
	* invalid token


---
Error making API request.

URL: GET http://0.0.0.0:8200/v1/sys/internal/ui/mounts/secret/anythingllm
Code: 403. Errors:

* 2 errors occurred:
	* permission denied
	* invalid token


```

### 7.3 cAdvisor state
```
cadvisor | Up 3 minutes (healthy) | 0.0.0.0:8088->8080/tcp, [::]:8088->8080/tcp
  /healthz http=200
  /metrics first line: # HELP cadvisor_version_info A metric with a constant '1' value labeled by kernel version, OS version, docker version, cadvisor version & cadvisor revision.
```

### 7.4 vmagent UP target count
```
  UP: 4 / total: 5
  caddy: up
  cadvisor: up
  mcp-docs: down
  node-exporter: up
  vmagent: up
```

### 7.5 git untracked + pre-block files
```
 M .gitignore
D  docker/caddy/Caddyfile.pre-block1
 M docker/observability-stack.yml
 M docker/vmagent-config/scrape.yml
D  docker/vmagent-config/scrape.yml.pre-block1
?? docs/phase-13/PHASE_13_BLOCK_1_5_RESULTS_2026-04-29.md

*.pre-block* files:
```

### 7.6 Audit results
  ❌ Vaultwarden keys: 
  ❌ secret/grafana/api missing
  ❌ secret/anythingllm/api missing
  ✅ cAdvisor: Up 3 minutes (healthy)
  ✅ vmagent UP targets: 4 (≥ 3)
  ✅ no *.pre-block* files in tree
