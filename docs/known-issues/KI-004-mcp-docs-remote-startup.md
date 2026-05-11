---
ki: KI-004
title: mcp-docs-remote startup fragility (apt-get + npm on every restart)
severity: LOW
status: MITIGATED
disposition: accept-as-permanent-debt-mitigated-workaround
discovered: 2026-04-29
phase: Phase 14 D-DOC
---

# KI-004: mcp-docs-remote startup fragility

## Symptom

`mcp-docs-remote` runs `apt-get update && apt-get install python3 make g++ curl && npm install -g @arabold/docs-mcp-server` on every container start. This causes:

1. Cold-start latency: 60–180 s before the server is ready (hence `start_period: 180s` in healthcheck)
2. Native-compilation failures on Colima: `EPERM: operation not permitted, futime` during node-gyp header tarball extraction
3. Dependency on live apt mirrors and npm registry at startup; network partition → crash loop

## Root Cause

The service uses `node:22-slim` (no tools pre-installed) and installs everything in the entrypoint `command:` block. No pre-built image exists for `@arabold/docs-mcp-server`; the install also attempts native tree-sitter compilation.

## Mitigation Applied (Phase 14 D-DOC)

Added `--ignore-scripts` to the npm install:

```yaml
command:
  - sh
  - -c
  - "apt-get update -qq && apt-get install -y -qq python3 make g++ curl && npm install -g --ignore-scripts @arabold/docs-mcp-server && npx -y supergateway ..."
```

This skips node-gyp native compilation. `@arabold/docs-mcp-server` uses `better-sqlite3` which ships pre-compiled binaries for common architectures; tree-sitter falls back to its JS implementation. The service now reaches healthy state.

## Recommended Fix (deferred)

Build a custom image that pre-installs `@arabold/docs-mcp-server` at build time:

```dockerfile
FROM node:22-slim
RUN apt-get update -qq && apt-get install -y -qq python3 make g++ curl \
    && npm install -g --ignore-scripts @arabold/docs-mcp-server \
    && apt-get purge -y python3 make g++ \
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
CMD ["npx", "-y", "supergateway", "--stdio", "docs-mcp-server", \
     "--outputTransport", "streamableHttp", "--port", "8093", \
     "--cors", "--healthEndpoint", "/healthz"]
```

Push to a local registry (e.g., `192.168.10.145:5000/iap/mcp-docs-remote:latest`) and reference it in `obot-stack.yml`. This reduces cold start to <5 s and eliminates the apt + npm network dependency.

## Impact

- No data loss risk
- Service is functional post-mitigation
- Cold-start latency remains elevated (~60 s for apt even with --ignore-scripts)
- Restart loop eliminated

## Disposition (2026-05-11)

Recorded per phase-17-closeout-audit §6 Q7: accept-as-permanent-debt. The `--ignore-scripts` mitigation is operationally functional; the recommended permanent fix (custom pre-built Docker image at `192.168.10.145:5000/iap/mcp-docs-remote:latest`) is deferred indefinitely. Reopens if mitigation fails or if operator schedules the custom-image build as a Phase 18 deliverable.
