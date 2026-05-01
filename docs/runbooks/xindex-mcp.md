# Runbook — xindex-mcp (D-16-02.3)

| Field            | Value                                            |
|------------------|--------------------------------------------------|
| Service          | xindex-mcp                                       |
| Image            | iap/xindex-mcp:0.1.0                             |
| Container        | xindex-mcp                                       |
| Network          | control-center-net                               |
| Bind             | 127.0.0.1:8096                                   |
| Caddy site       | https://mcp-xindex.internal                      |
| Backend          | http://xindex:8000 (XINDEX_BASE_URL)             |
| Compose          | `docker/xindex-mcp/docker-compose.yml`           |
| NetBox service   | id=77, device=mac-mini, port=8096                |
| Status           | LIVE 2026-05-01                                  |

## §1 — Purpose

Closes the cross-index foundation chain (D-16-02 → 02.0.5 → 02.A → 02.1
→ 02.2 → 02.3). xindex itself exposes a normalized HTTP surface over the
repo's docs + NetBox + Plane state; xindex-mcp wraps that surface as an
MCP (Model Context Protocol) server so any MCP-aware agent — Claude
Code, Claude.ai, Obot — can query it natively via tool calls without any
prior knowledge of the URL or curl.

This is the structural enabler for autonomous coding: an agent fixing a
bug or extending a feature first needs to *understand* the system, and
the system's truth lives in xindex.

## §2 — Architecture

```
┌─────────────────┐         ┌──────────┐         ┌──────────────────┐
│  Agent (Claude  │ stdio   │  xindex- │ HTTP    │  xindex          │
│  Code, Obot,    │ ──────▶ │  mcp     │ ──────▶ │  127.0.0.1:8095  │
│  Claude.ai)     │ JSONRPC │  server  │ /search │  /adr, /service, │
└─────────────────┘         └──────────┘ /adr…   │  /plane, /links… │
                                  ▲              └──────────────────┘
                            ┌─────┴─────┐
                            │supergateway│  for non-stdio clients (Obot,
                            │stdio→HTTP  │  Caddy-fronted /mcp endpoint)
                            └────────────┘  on :8096
```

- The same Python server (`docker/xindex-mcp/app/server.py`, stdlib only)
  serves both stdio (for Claude Code; one process per session) and the
  containerized HTTP transport (one long-lived container; supergateway
  multiplexes JSON-RPC over streamableHttp on `/mcp`).
- xindex-mcp depends on xindex; if xindex is down, every tool returns
  `isError: true` with the underlying HTTP failure surfaced — calling
  agents back off rather than retrying.
- xindex-mcp is **read-only by design** (ADR-A-006: xindex never writes
  to Plane; xindex-mcp's MCP surface inherits that). No `/refresh` tool
  is exposed; periodic refresh is the platform's job.

## §3 — Tool reference

All tools accept JSON arguments and return a JSON body inside the MCP
`content[0].text` field (pretty-printed). Tool names use snake_case.

### `xindex_search(query, type='all', limit=20)`
FTS5 search. `type ∈ {all, adr, runbook, register, service, node,
plane_issue}`. Returns ranked SearchResult rows.

```json
{"name": "xindex_search", "arguments":
  {"query": "vault unseal", "type": "runbook", "limit": 5}}
```

### `xindex_get_adr(adr_id)`
Full ADR detail. Accepts `A-NNN` or `ADR-A-NNN`. Includes
`register_entry` (DECISION_REGISTER row) and `plane_tracking` (Plane
issue state) when present.

```json
{"name": "xindex_get_adr", "arguments": {"adr_id": "A-006"}}
```

### `xindex_get_runbook(topic)`
Runbook by filename stem (e.g. `vault-unseal`, `xindex-mcp`).

### `xindex_get_service(name)`
NetBox service detail with custom fields and entity_links
(`hosted_on`, `depends_on`, `governs`).

### `xindex_get_node(name)`
NetBox device with services hosted on it.

### `xindex_get_plane(external_id)`
Plane issue (e.g. `D-16-02.2`, `ADR-A-006`, `Phase-16`) — state, module,
description, inbound `tracked_in` links.

### `xindex_get_links(from_kind?, from_ref?, to_kind?, to_ref?, link_type?, source?)`
Filter `entity_links`. All filters optional; with no filters returns
the first 100. Use for traversal:

```json
{"name": "xindex_get_links", "arguments":
  {"from_kind": "deliverable", "link_type": "tracked_in"}}
```

### `xindex_health()`
`/healthz` — per-source `last_ingest_at`, `status`, `error`, plus row
counts. **Call this before relying on a query result if freshness
matters.**

## §4 — Configuration

### Claude Code

Per-operator (current state):

```bash
cd /Users/admin/repos/integrated-ai-platform
claude mcp add xindex python3 \
  /Users/admin/repos/integrated-ai-platform/docker/xindex-mcp/app/server.py \
  -e XINDEX_BASE_URL=http://127.0.0.1:8095
```

Verify:

```bash
claude mcp list | grep xindex
# xindex: python3 .../docker/xindex-mcp/app/server.py - ✓ Connected
```

A repo-tracked `.mcp.json` was considered but deferred — the operator's
preference was to keep MCP registrations explicit per host. Future work
to add a committed `.mcp.json` is captured in §7.

### Claude.ai (Settings → Connectors → MCP)

```
Name:    xindex
Command: python3 /Users/admin/repos/integrated-ai-platform/docker/xindex-mcp/app/server.py
Env:     XINDEX_BASE_URL=http://127.0.0.1:8095
```

### Obot / generic HTTP MCP client

Use the streamableHttp transport on port 8096:

```
URL:       http://host.docker.internal:8096/mcp
Transport: streamableHttp
```

Caddy also serves it at `https://mcp-xindex.internal` (signed by the
internal CA — see `docs/runbooks/caddy-tls.md`).

## §5 — Debugging

### Direct stdio test (no MCP client needed)

```bash
{ echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
} | XINDEX_BASE_URL=http://127.0.0.1:8095 \
    python3 docker/xindex-mcp/app/server.py
```

Should print two JSON-RPC reply lines — `serverInfo` and the eight tool
definitions.

### HTTP transport test

```bash
curl -sS -X POST http://127.0.0.1:8096/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"xindex_health","arguments":{}}}'
```

Reply is an SSE-formatted JSON-RPC response (`event: message\ndata: ...`).

### Container logs

```bash
docker logs xindex-mcp --tail 50
```

supergateway logs every request and response on stderr; the inner
Python server logs to stderr too (errors only — no per-request logs by
design).

### Tests

```bash
cd /Users/admin/repos/integrated-ai-platform/docker/xindex-mcp
/tmp/xindex-test-env/bin/python -m pytest app/tests -q
# 20 passed (or 18 + 2 skipped without XINDEX_BASE_URL set)

# Smoke against a live xindex:
XINDEX_BASE_URL=http://127.0.0.1:8095 \
    /tmp/xindex-test-env/bin/python -m pytest app/tests/test_smoke_e2e.py -q
```

## §6 — Recovery

xindex-mcp is stateless — no DB, no creds, no volumes. Recovery is
always: rebuild image, restart container.

```bash
cd /Users/admin/repos/integrated-ai-platform/docker/xindex-mcp
docker compose down
docker compose build
docker compose up -d
docker compose ps          # confirm healthy
curl -sS http://127.0.0.1:8096/healthz   # → "ok"
```

If xindex itself is down, xindex-mcp will return per-tool errors but
will stay running — the operator can still call xindex directly:

```bash
curl -sS http://127.0.0.1:8095/healthz | jq    # raw HTTP, no MCP
```

This is the documented fallback for human callers; agents see the same
information via `xindex_health`.

## §7 — Future tools

Captured here so they aren't re-discovered later:

- `xindex_get_all_adrs()` — list endpoint with status filter; today
  agents must `xindex_search` for ADRs which gets ranked, not enumerated
- `xindex_traverse_links(start_kind, start_ref, depth=2)` — multi-hop
  link traversal in one call (today is N+1 round-trips)
- `xindex_get_phase(name)` — phase deliverable rollup (counts by
  status); already in xindex via `/plane/module/{name}` but a phase-
  centric tool would be clearer to the agent
- `xindex_get_decision_register_entry(adr_id)` — the DR row alone, when
  the full ADR body is too much context

Generalization opportunity (when a third NetBox service register is
needed, this becomes worth doing):

- `scripts/netbox-register-service.py` — argv-driven, replaces the
  near-duplicate `netbox-register-xindex.py` and
  `netbox-register-xindex-mcp.py`. Currently two near-clones is cheaper
  than the abstraction.

A repo-tracked `.mcp.json` so the MCP registration travels with the
repo (instead of being per-operator-home only) — deferred 2026-05-01;
revisit once a second consumer host (Mac Studio) needs the same wiring.

## §8 — References

- `docs/adr/ADR-A-006-plane-and-repo-sources-of-truth.md` — read-only
  doctrine (xindex consumes Plane, never writes)
- `docs/runbooks/xindex.md` — backend HTTP service runbook
- `docs/runbooks/add-new-service.md` — generic service onboarding
  template (xindex-mcp followed it)
- `docker/xindex-mcp/Dockerfile`, `.../docker-compose.yml`,
  `.../app/server.py`
- `scripts/netbox-register-xindex-mcp.py` — NetBox CMDB registration
