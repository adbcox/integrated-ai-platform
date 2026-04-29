# Phase 13 Block 3 P6 — Mac Mini CATT Controller Stack

**Date**: 2026-04-29
**Operator**: claude-opus-4-7[1m]
**Scope**: platform-layer Cast control HTTP API, no devices.

---

## Architecture decision: single controller, not three

The pre-block-3 audit (§A.4) proposed three CATT containers on 8124–8126: `catt-controller`, `catt-receiver-display`, `catt-receiver-events`. Investigation showed:

- **`catt-receiver-display`** as framed (a "receiver" service) is conceptually wrong. Cast targets ARE the receivers. There is no platform-side "receiver" component.
- **`catt-receiver-events`** would only have value if the controller maintained persistent Cast sessions and broadcast their state changes, which adds runtime complexity for an unclear use case (HA already exposes Cast state via `media_player.*` entities — duplicate work).

Settled on **one** service: `catt-controller` on 8124. Ports 8125 and 8126 are left free for future additive services if a real need surfaces. The compose stack at `~/control-center-stack/stacks/catt/` is structured to make adding services trivial — no path-rename or restructure later.

This is a deliberate scope-tightening, not a deferral. The 3-container framing was speculative in the audit; the 1-container delivery is the platform value.

---

## Deliverable inventory

| File | Purpose |
|---|---|
| `~/control-center-stack/stacks/catt/Dockerfile` | python:3.13-slim-bookworm base; non-root user (uid 10001) |
| `~/control-center-stack/stacks/catt/requirements.txt` | catt 0.12.13 + fastapi 0.115.6 + uvicorn 0.34.0 + pychromecast 14.0.5 (all pinned) |
| `~/control-center-stack/stacks/catt/app.py` | FastAPI app — `/healthz`, `/cast`, `/pause`, `/resume`, `/stop`, `/volume`, `/status` |
| `~/control-center-stack/stacks/catt/docker-compose.yml` | hardened compose entry (cap_drop ALL, no-new-privileges, read_only, mem_limit 256m) |
| `docker/caddy/Caddyfile` (lines 274–281) | new `catt.internal` route → `host.docker.internal:8124` |
| `docs/phase-13/p6-rewire/pre-snapshot.txt` | docker ps before deploy (47 lines) |
| `docs/phase-13/p6-rewire/post-snapshot.txt` | docker ps after deploy (48 lines) |

Per CLAUDE.md doctrine: out-of-repo compose changes (`~/control-center-stack/stacks/catt/`) tracked with pre/post snapshots since git doesn't see them.

---

## Endpoint reference

All endpoints accept JSON. No auth (LAN-internal).

| Method | Path | Body | Behavior |
|---|---|---|---|
| GET | `/healthz` | n/a | 200 `{"status": "ok"}` |
| POST | `/cast` | `{device_ip, url, content_type?, title?}` | start playback of arbitrary URL |
| POST | `/pause` | `{device_ip}` | pause current media |
| POST | `/resume` | `{device_ip}` | resume |
| POST | `/stop` | `{device_ip}` | stop + quit Cast app |
| POST | `/volume` | `{device_ip, level}` | level ∈ [0.0, 1.0] |
| POST | `/status` | `{device_ip}` | returns device + media status |

Errors return HTTP 502 with `detail: <type>: <msg>`. No retries — caller (HA) owns retry logic.

---

## Verification (this session)

```
$ curl -s http://127.0.0.1:8124/healthz
{"status":"ok"}

$ docker ps --filter name=catt-controller --format '{{.Names}} | {{.Status}}'
catt-controller | Up 22 seconds (healthy)

$ curl -sk --resolve catt.internal:443:127.0.0.1 https://catt.internal/healthz
{"status":"ok"}
HTTP 200
```

End-to-end Caddy route working. Compose snapshot diff (post-pre) shows only `catt-controller` added, nothing else disturbed.

---

## Hardening

- `cap_drop: [ALL]`, no `cap_add`
- `security_opt: [no-new-privileges:true]`
- `read_only: true` with `tmpfs:/tmp:size=64m`
- Non-root user `catt` uid 10001 inside container
- `mem_limit: 256m`
- Pinned image tag `iap/catt-controller:1.0.0` (locally built, no `:latest`)
- No credentials → no Vault Agent sidecar required

---

## Out-of-scope (rolled forward)

- HA `rest_command:` config-entry to consume the API — that's HA-side device-population work
- yt-dlp source resolution endpoint (`/cast` accepts only direct URLs today; resolving YouTube/etc URLs server-side would expand attack surface and is best left to the caller)
- Cast device discovery (mDNS doesn't bridge through Docker Desktop on macOS — workaround documented in `app.py`: callers pass `device_ip` directly, sourced from HA's own Cast integration)
- Multi-receiver coordination (groups, ad-hoc multi-room) — additive; would justify the deferred 8125/8126 port slots
