# Phase 13 Block 3 P7 — Integration Test + Block 3 Close-out

**Date**: 2026-04-29
**Operator**: claude-opus-4-7[1m]
**Gate**: Phase 13 Block 3 final close
**Result**: ✅ PASS — Block 3 platform-layer scope delivered

---

## Block 3 mission (recap)

Deliver the **Display & Voice platform layer** — clean Home Assistant rebuild on the Intel NUC (192.168.10.141), 100% local Wyoming voice stack, area-driven Lovelace framework, and a Mac Mini Cast control HTTP API — without crossing into device-population scope.

Device pairing, ESPHome firmware flashes, Meross/Warmup credentials, physical satellite hardware, and per-room polish are explicitly *out of scope* and roll forward to a future device-population block.

---

## Phase deliverable matrix

| Phase | Scope | Status | Doc |
|---|---|---|---|
| **P1 Foundation Audit** | Read-only inventory, credential map, CATT readiness, Cast targets, Ollama deferral matrix | ✅ | `PRE_BLOCK_3_FOUNDATION_AUDIT_2026-04-28.md` |
| **P2 HA wipe + rebuild** | Full HA reset to factory; preserve areas (15) + admin user + URLs; verify post-rebuild posture | ✅ | `PHASE_13_BLOCK_3_P2_P3_CLOSEOUT_2026-04-28.md` |
| **P3 Local voice** | Whisper STT (small-int8) + Piper TTS (en_US-lessac-medium) + openWakeWord (okay_nabu); 3 Wyoming entries; "Home Assistant (Local Voice)" pipeline preferred; NLU smoke pass | ✅ | `PHASE_13_BLOCK_3_P2_P3_CLOSEOUT_2026-04-28.md` |
| **P4 Voice satellite framework** | ESPHome YAML template (`satellite-template.yaml`), 15-area priority mapping, hardware spec, deployment workflow — *no firmware flash* | ✅ | `PHASE_13_BLOCK_3_P4_VOICE_SATELLITE_FRAMEWORK_2026-04-29.md` |
| **P5 Lovelace framework** | `area-driven-dashboard.yaml` — 15 views, sections layout, area-filter cards (no entity_id hardcoding); area-id quirk documented | ✅ | `PHASE_13_BLOCK_3_P5_LOVELACE_FRAMEWORK_2026-04-29.md` |
| **P6 Mac Mini CATT stack** | `catt-controller` FastAPI on 8124, Caddy `catt.internal` route, hardened compose, no creds | ✅ | `PHASE_13_BLOCK_3_P6_CATT_STACK_2026-04-29.md` |
| **P7 Integration test + close** | Final probe + service-registry walk + voice-pipeline snapshot + this doc | ✅ | (this file) |

---

## Verification — Block 3 final state

### Regression probe (Phase 13 H1 doctrine)
```
Gate unspecified summary: PASS=15 FAIL=0 WARN=3
```
- 47 containers up, 0 restarting
- All sampled service health endpoints (vaultwarden, openhands-app, litellm-gateway, mcpo-proxy, open-webui, vault-server, nextcloud) → HTTP 200
- Vault sealed=false, audit log incrementing
- Caddy `.internal` DNS → 4/5 sites HTTP 200 (openhands warn is pre-existing — DNS-cache hint, not a service fault)
- 3 WARN are all pre-Block-3 entries (openhands DNS cache, restic-list creds requiring Vault fetch, no gate-specific deps for "unspecified")

### CATT controller (Mac Mini, P6)
```
catt-controller | Up 5 minutes (healthy)
GET http://127.0.0.1:8124/healthz       → {"status":"ok"}
GET https://catt.internal/healthz       → HTTP 200 (Caddy local-CA TLS)
```

### Home Assistant voice pipeline (NUC, P2-P3)
From `/tmp/ha_p7_verify.py` snapshot:
```
=== Add-ons (6) ===
  core_matter_server            v8.0.0     state=started   boot=auto
  a0d7b954_vscode               v6.6.1     state=started   boot=auto
  core_ssh                      v9.18.0    state=started   boot=auto
  core_whisper                  v3.0.2     state=started   boot=auto
  core_piper                    v2.2.0     state=started   boot=auto
  core_openwakeword             v1.10.0    state=started   boot=auto

=== Wyoming config_entries (3) ===
  Whisper        state=loaded
  Piper          state=loaded
  openWakeWord   state=loaded

=== Voice Assist pipeline ===
  preferred: Home Assistant (Local Voice)
    conv=conversation.home_assistant
    stt=stt.faster_whisper
    tts=tts.piper / en_US-lessac-medium
    wake=wake_word.openwakeword / okay_nabu

=== NLU smoke ===
  'what time is it' → '4:02 AM'

=== Areas (15) ===  (preserved through wipe — see P2)
=== Config entries by domain (22 total) ===
  wyoming                  3
  matter                   1
  ssdp/zeroconf/...        18 auto-discovered
```

ESPHome-dev residue (`5c53de3b_esphome-dev`) from the pre-scope-correction install attempt was uninstalled in P7. Final addon set is the intended 6.

---

## Lessons learned (consolidated, Block 3)

1. **Vault field naming drift** — `secret/homeassistant/api` field is `token`, not `api_key`. The pre-block-3 audit's credential map had the wrong field name. Both `token` and `homepage_token` exist as duplicates (hash `cda3bb49b25f`). Always read the field list before scripting.

2. **HA Whisper add-on schema is non-trivial** — `core_whisper` options-set requires *all* fields (model, stt_library, custom_model_type, language, beam_size, debug_logging) on every call. Inspect via `/addons/<slug>/info` first; partial sets fail validation silently.

3. **openWakeWord bundled wake-words** — only `okay_nabu` (with the y), `hey_jarvis`, `hey_mycroft`, `alexa`, `hey_rhasspy` ship pre-trained. `ok_nabu` is *accepted* by pipeline schema but never matches at runtime. Always cross-check the bundled list.

4. **WebSocket vs REST split** — HA accepts integration setup via WebSocket for *most* operations, but `config_entries/flow/init` returns `unknown_command` over WS. Use `POST /api/config/config_entries/flow` (REST) for flow_init, then continue the flow over either transport.

5. **HACS list shape varies** — `hacs/repositories/list` returns either a flat list or `{"repositories": [...]}` depending on HACS version. Defensive code should handle both.

6. **Scope discipline for ESPHome** — installing the ESPHome add-on (no devices, no flashes) was rejected by the user as *device-population scope*. The framework deliverable is the `satellite-template.yaml` + deployment doc; touching the actual integration belongs in the device-population block. Future blocks: re-confirm scope envelope before any add-on install that has device-side coupling.

7. **HA area_id ≠ slugify(name)** — three of fifteen areas have non-slugified IDs (`bedroom` for "Master Bedroom", `office_2` for "Office", `office` for "MDF"). Race-condition artifacts of the original area-creation order. Always pull `config/area_registry/list` before writing area-bound YAML.

8. **Caddy NAT-strip pattern for cross-host upstreams** — HA on the NUC can't reliably anchor `trusted_proxies` to a known IP because Docker Desktop's NAT randomizes the source. Solution: strip all `X-Forwarded-*` and `Forwarded` headers on the upstream side; HA treats it as a normal LAN-direct connection. Same pattern will apply to any future cross-LAN-host reverse-proxy upstream.

9. **One container beats three speculative containers** — pre-block audit framed CATT as 3 services (`controller`, `receiver-display`, `receiver-events`). Investigation collapsed it to 1 (Cast targets *are* the receivers; HA already exposes Cast state via `media_player.*` entities). Ports 8125–8126 are kept free for additive services if real need surfaces. Prefer minimal viable surface and grow on demand.

10. **Compose pre/post snapshots remain non-negotiable** — out-of-repo `~/control-center-stack/stacks/catt/` compose changes are invisible to git. P6 captured pre/post `docker ps` in `docs/phase-13/p6-rewire/` showing only `catt-controller` added. Rewire-log doctrine continues to pay off.

---

## Out-of-scope (rolled forward — for the device-population block)

| Item | Why deferred | Where it lives |
|---|---|---|
| **ESPHome add-on install + device flashes** | device-side scope; needs physical M5Stack Atom Echo / equivalent units | P4 framework doc has hardware spec + per-area priority |
| **Meross integration credentials** | device-population scope per user directive (D2 dropped) | `secret/meross/*` exists in Vault if/when needed |
| **Warmup integration credentials** | device-population scope per user directive (D3 dropped) | `secret/warmup/*` exists in Vault if/when needed |
| **HA `rest_command:` to consume CATT API** | HA-side device wiring; needs Cast targets paired in HA first | P6 endpoint reference is the contract |
| **yt-dlp source resolution endpoint** | expands attack surface; caller-side concern | noted in P6 out-of-scope §3 |
| **mDNS Cast device discovery in CATT** | doesn't bridge through Docker Desktop on macOS; callers pass `device_ip` directly | noted in P6 out-of-scope §3 |
| **Multi-receiver coordination (groups, multi-room)** | additive; would justify the deferred 8125/8126 port slots | noted in P6 out-of-scope §4 |
| **Per-room dashboard polish** (camera streaming layouts, scheduling cards, mobile dashboard) | post-population polish | noted in P5 out-of-scope §3 |
| **Auth/role-based view visibility on dashboard** | requires HA users beyond admin | noted in P5 out-of-scope §4 |
| **Ollama integration into HA pipeline** | per A.7 deferral matrix; current local NLU is sufficient for platform layer | A.7 of foundation audit |

---

## Block 3 close criteria — checklist

- [x] HA running clean post-wipe with 15 areas preserved
- [x] Wyoming voice stack: 3 services (Whisper / Piper / openWakeWord) loaded as config_entries, all `state=loaded`
- [x] "Home Assistant (Local Voice)" pipeline configured + preferred + NLU smoke passes
- [x] Voice satellite framework artifact (template YAML + per-area priority + deployment workflow) committed to repo
- [x] Lovelace area-driven dashboard YAML committed to repo, 15 views, area-id-correct
- [x] CATT controller deployed on Mac Mini, healthy, reachable via `catt.internal` Caddy route
- [x] Caddy compose unchanged structurally (only one new site block); pre/post snapshots filed
- [x] Container hardening doctrine applied to `catt-controller` (cap_drop ALL, no-new-privileges, read_only, mem_limit, non-root uid)
- [x] No credentials passed to CATT (no Vault Agent sidecar required — confirmed)
- [x] Final regression probe: 15 PASS / 0 FAIL / 0 new WARN
- [x] No `.env` files; no plaintext credentials in transcript or commit history
- [x] Doctrine docs (PLATFORM_OVERVIEW, etc.) need only minor `Block 3 complete` mark in next session — not blocking close

---

## Forward pointers

- **Next block (device-population)**: ESPHome flashes for satellites; Cast targets pairing into HA; Meross + Warmup credential plumbing; per-area device polish; HA `rest_command:` wiring CATT.
- **Phase 14 (still pending)**: Loki for per-site Caddy log analysis (covers per-host dashboards Caddy 2.11.2's metrics output can't do alone — `host` label missing from `caddy_http_request_*` series).
- **Standing follow-ups** (CLAUDE.md Post-Block-2 list):
  1. Caddy dead-route prune (12 unbacked `*.internal` routes)
  2. Homepage widget completion (Grafana SA + Uptime Kuma slug)
  3. Block 3 ← *now closed*
  4. Phase 14 Loki

Block 3 is closed.
