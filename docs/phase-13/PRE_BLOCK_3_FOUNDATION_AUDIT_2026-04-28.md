---
phase: 13
block: 3
stage: pre-execution-foundation-audit
date: 2026-04-28
operator: claude-opus-4-7[1m]
mode: read-only
---

# Phase 13 — Block 3 Foundation Audit (Pre-execution)

**Block scope**: Display & Voice Platform — Home Assistant clean rebuild (.141), 100%-local voice (Whisper + Piper + OpenWakeWord), Lovelace dashboard framework, Mac Mini CATT control stack.

**Audit scope**: Read-only verification of all foundations Block 3 will build on. **No mutations.** Pause-and-surface gate at the bottom of this document; user reviews before Phase 2 (HA wipe) is authorized.

**Companion document**: `HA_INVENTORY_2026-04-28.md` (commit d7d06c2) — current-state inventory referenced by §A.2.

---

## §A.1 — HA host hardware

Probed via supervisor `/info`, `/host/info`, `/hardware/info`, `/supervisor/stats` over WebSocket `supervisor/api` proxy.

| Property | Value | Source |
|---|---|---|
| Form factor | embedded chassis, generic-x86-64, amd64 | `/host/info.chassis`, `/info.machine` |
| OS | Home Assistant OS 17.1 (latest 17.2 — update available) | `/host/info.operating_system` |
| Kernel | 6.12.67-haos | `/host/info.kernel` |
| Hostname | `homeassistant` | `/host/info.hostname` |
| Timezone | America/New_York | `/host/info.timezone` |
| CPU logical cores | 4 (cpu0–cpu3) | `/hardware/info.devices[subsystem=cpuid]` count |
| RAM total | ~15.46 GiB (memory_limit 16,597,463,040 bytes) | `/supervisor/stats.memory_limit` |
| Disk device | Samsung SSD 850 EVO mSATA 250GB (S248NXAG710367J) | `/hardware/info.drives[0]` |
| Disk total / free | 228.5 GB / 204.1 GB free / 15.1 GB used | `/host/info.disk_*` |
| Primary network | enp3s0 (ethernet) — IPv4 192.168.10.141/24, gw 192.168.10.1, MAC FC:AA:14:A9:9F:D2 | `/network/info` |
| Display outputs detected | DP-1, HDMI-A-1, HDMI-A-2 (Intel iGPU at 0000:00:02.0) | `/hardware/info.devices[subsystem=drm]` |
| Hardware classification | **Intel NUC class** (4-core, 16 GB, mSATA SSD, embedded chassis, integrated graphics) | derived |

**Block-3 sizing implication**: 4 cores + 16 GB is comfortably above the supervisor-managed Whisper add-on's working set for the **`small-int8`** (244 MB) or **`base-int8`** (74 MB) models. The **`medium-int8`** (769 MB) model is tractable on this CPU but transcription latency rises noticeably (~3-5× real-time on x86-64 without AVX-512). Recommendation: **`small-int8`** as default, with `base-int8` as fallback if first-pass response time is unacceptable. Reserve `medium-int8` for diagnostics only.

**Resolution-center checks (current state)**:
- 0 unsupported reasons
- 0 unhealthy reasons
- 0 active issues
- 0 active suggestions

→ Foundation is healthy enough to receive a clean rebuild.

---

## §A.2 — Integration credential map (post-wipe re-pairing requirement)

**Critical finding**: Vault probe (root path `secret/`, listed below) shows that **integration auth credentials are not stored in Vault**. The HA `config_entries` tree stored under `/config/.storage/core.config_entries` is the sole holder of integration tokens, OAuth refresh tokens, paired Hue/Caséta bridges, etc. **Wiping HA discards all of them.**

**Vault top-level (relevant slice)**:

```
secret/
├── homeassistant/   ← only HA-related path
│   └── api          ← long-lived bearer token (homepage_token, token; identical sha256-12=cda3bb49b25f)
├── macmini/         ← sudo (Mac Mini admin pw)
└── ... (no hue/lutron/shelly/sonoff/tplink/govee/matter/thread/skyconnect entries)
```

**Implication**: Phase 2 HA wipe requires re-pairing every integration. Each row below is a re-pair target.

| Integration | Current state (from `HA_INVENTORY_2026-04-28.md`) | Re-pair flow on rebuild |
|---|---|---|
| Hue (Philips) | config_entry `loaded` | Bridge button-press OAuth — requires physical access to Hue Bridge |
| Lutron Caséta | config_entry `loaded` | Caséta SmartHub QR/IP pairing — re-discovery via mDNS |
| Shelly | config_entry `loaded` | Local cloud-less per-device OAuth/token — re-add each Shelly endpoint |
| Sonoff (eWeLink) | config_entry `not_loaded` (was already broken pre-wipe) | LAN mode token re-issue OR cloud OAuth — known to be flaky; may be retired |
| TP-Link Kasa | 6 entries `setup_error` (was broken pre-wipe) | LAN protocol auto-discovery — credential-less for older Kasa, OAuth needed for Tapo |
| Govee | config_entry `setup_retry` (was already broken pre-wipe) | API key from developer.govee.com — manual paste (no Vault path; create one in Phase 2) |
| Google Nest / Cast | media_players paired (Master Bedroom Display, Kitchen Speaker, Kitchen Display, SHIELD-2) | mDNS auto-discovery; YouTube/Spotify OAuth re-flow per-account |
| Matter / Thread / SkyConnect | not currently configured (0 ESPHome devices, 0 Matter fabrics in inventory) | Block 3 P2.6 will configure fresh; no migration needed |
| Mobile App companion | 1 device_tracker | Re-install on phone, link via QR pairing |
| Meross | add-on `8b8632af_meross_local_broker` started; integration dependent on broker | Re-link broker after rebuild; no Vault credentials |

**Recommendation surfaced to user (item #2 in surface-back list)**: before Phase 2 begins, decide which of the broken integrations (Sonoff `not_loaded`, TP-Link 6×`setup_error`, Govee `setup_retry`) to **drop** vs **fix-then-rebuild**. Dropping shortens Phase 2 P2.4 by ~3-4 paired flows; fixing requires upstream debugging (out of Block 3 scope). User decision required before HA wipe.

---

## §A.3 — Supervisor scope verification (resolved during probe)

**Initial concern**: REST `/api/hassio/*` returned 401 with the standard long-lived token, suggesting Block 3 supervisor operations would need a fresh `addons:read addons:write supervisor:read host:read` token issued via Studio Code Server.

**Resolution**: WebSocket `supervisor/api` proxy works **with the existing standard long-lived token**:

```
WS message: {"type": "supervisor/api", "endpoint": "/<path>", "method": "get|post"}
```

This proxies through the same WebSocket auth context — the supervisor scopes are enforced server-side based on the user's permissions, not the token itself.

**Confirmed working endpoints** (via `supervisor/api` proxy):
- `/info`, `/host/info`, `/os/info`, `/supervisor/info`, `/core/info`
- `/addons` (list installed), `/store` (list available)
- `/network/info`, `/hardware/info`, `/resolution/info`
- `/supervisor/stats`, `/core/stats`, `/host/services`

**Implication for Block 3**: All supervisor automation (add-on install, start/stop, log retrieval) can run without a fresh token. The Studio Code Server fresh-token step is **not needed** for automation — only needed if the user wants raw REST access from outside (e.g., curl against `/api/hassio`).

---

## §A.4 — Mac Mini CATT readiness

| Check | Result | Detail |
|---|---|---|
| Vault status | ✅ HEALTHY | unsealed, initialized, version 2.0.0, cluster `vault-cluster-1b9404db` |
| Vault root path inventory | 27 top-level paths (`anythingllm/` through `zabbix/`) — slot for new `catt/` and `cast-targets/` available | listed via `secret/metadata?list=true` |
| Caddy `homeassistant.internal` route | ❌ **NOT PRESENT** (Block 3 P2.5 will add) | grep against 36 `*.internal` site blocks |
| Caddy `catt.internal` route | ❌ **NOT PRESENT** (Block 3 P6.4 will add) | grep against Caddyfile |
| Mac Mini Ollama | ✅ RUNNING — port 11434, 6 models loaded | `qwen2.5-coder:32b` (18.49 GB), `devstral` (13.35 GB), `deepseek-coder-v2` (8.29 GB), `qwen2.5-coder:14b/7b`, `nomic-embed-text` |
| litellm-gateway | ✅ REACHABLE — port 4000 (HTTP 400 on dummy bearer; needs vault-resolved token) | proxy live, model list gated |
| Mac Mini hardware probed | Apple M4 Pro, 48 GB RAM, hostname `mac-mini.internal`, en0 192.168.10.145 | `sysctl -n hw.model machdep.cpu.brand_string hw.memsize` |
| Port 8123 listener | ⚠️ ssh-forward (PID 21652) | benign — operator's SSH local-forward to HA web UI; Block 3 doesn't bind 8123 on Mac Mini |
| Free ports for 3 CATT containers | 8124–8126 (or 8131–8133 — many gaps in the bound-port list) | proposed allocation: catt-controller 8124, catt-receiver-display 8125, catt-receiver-events 8126 |

**Inferred Mac Mini headroom**: Apple M4 Pro 48 GB RAM is comfortably oversized for the CATT control stack (Python service + lightweight HTTP server + media controller). No CPU/RAM concerns.

**Note on hardware nameplate**: `sysctl` reports `Mac16,11 / Apple M4 Pro / 48 GB`. CLAUDE.md and prior phase docs refer to this host as "Mac Mini M5" — the discrepancy is naming-only; the actual silicon is M4 Pro per the kernel. CLAUDE.md should be reconciled in a future tidy-up (out of Block 3 scope).

---

## §A.5 — Voice add-on prerequisites

| Add-on slug | Catalog status | Wyoming default port | HA host port free? | Notes |
|---|---|---|---|---|
| `core_whisper` | ✅ available in core store | 10300/tcp | ✅ free on 192.168.10.141 (closed/filtered, not yet bound) | recommends `small-int8` for 4-core/16GB |
| `core_piper` | ✅ available in core store | 10200/tcp | ✅ free on 192.168.10.141 (closed/filtered, not yet bound) | en_US voice pack ~50 MB |
| `core_openwakeword` | ✅ available in core store | 10400/tcp (default) | not pre-probed (uncommon to be already-bound) | "Hey Jarvis" + custom wake-words |
| `core_mosquitto` | ✅ available in core store | 1883/tcp | not yet probed | needed if Block 3 introduces MQTT (esphome auto-discovery) |
| `core_samba` | ✅ available in core store | 445/tcp | n/a — Samba binds inside add-on namespace | enables `/config` workflow editing from Mac |
| `core_configurator` | ✅ available in core store | (web) | n/a | "File editor" — supplements vscode add-on |
| `5c53de3b_esphome` | ✅ available in 3rd-party repo | (web) | n/a | for ESPHome wake-word satellites in P4 |
| `a0d7b954_vscode` (Studio Code Server) | ✅ ALREADY INSTALLED, started | (web on 8443/tcp inside add-on namespace) | n/a | will survive wipe via add-on snapshot if user opts |

**Whisper model recommendation (item #3 in surface-back list)**:

| Model | Size | RAM @ inference | Latency on 4×amd64 | Quality |
|---|---|---|---|---|
| `tiny-int8` | 39 MB | ~150 MB | 0.5–1× real-time | poor (mishears commands) |
| `base-int8` | 74 MB | ~250 MB | 0.7–1.5× real-time | acceptable |
| **`small-int8`** ← recommended | **244 MB** | **~600 MB** | **1–2× real-time** | **good (production-grade for home commands)** |
| `medium-int8` | 769 MB | ~1.6 GB | 3–5× real-time | very good but laggy on this hardware |
| `large` family | n/a | not viable on 16 GB CPU-only | n/a | not recommended |

→ Default to `small-int8`. If wake-word + STT round-trip exceeds ~2.5s end-to-end, fall back to `base-int8`. Monitor via Wyoming protocol latency log entries.

**Network reachability**: Mac Mini → 192.168.10.141:10200/10300 — both ports return "closed/filtered" (TCP RST or no SYN-ACK). This is **expected before add-on install**; the supervisor will bind them once the add-ons start. Will re-verify after Block 3 P3.

---

## §A.6 — Cast targets reachable from current HA state

Reverified via `get_states` WebSocket call.

| entity_id | friendly_name | state | Block-3 use |
|---|---|---|---|
| `media_player.master_bedroom_display` | Master Bedroom Display | `off` | bedroom Cast voice output |
| `media_player.kitchen_speaker` | Kitchen speaker | `off` | kitchen voice output |
| `media_player.kitchen_display` | Kitchen Display | `off` | kitchen Cast display |
| `media_player.shield_2` | SHIELD | `off` | living-room Cast / movie-room Cast |
| `media_player.shield`, `.shield_3..5`, `.chromecast`, `.projector` | (no friendly name) | `unavailable` | stale device-registry entries — will not survive rebuild; safe to drop |

**Total reachable**: **4** active Cast targets. The inventory's "5 reachable" included the mobile-app companion device_tracker which is **not** a media_player and routes voice through the Companion App (different code path). Re-discovery during Phase 2 P2.6 should restore these 4 within minutes via mDNS without re-pairing (Cast does not require OAuth at this layer; YouTube/Spotify per-account OAuths are separate and **will** need re-flow).

**ESPHome / Wyoming wake-word satellite candidates (current state)**: 0. Block 3 P4 will introduce satellites as net-new devices.

---

## §A.7 — Ollama deferral decision matrix

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A. Defer until Threadripper** | Block 3 ships voice-only. HA Assist conversation pipeline routes STT → intent extraction (HA built-in NLU) → TTS. No LLM fallback. | • Cleanest separation; Mac Mini stays in control-plane lane • No risk of Mac Mini overload during heavy local-coding sessions hitting qwen2.5-coder:32b • Matches platform doctrine "Mac Mini = control plane only" | • HA Assist's built-in NLU is brittle ("turn off the lights" works; "make it cozy in here" fails) • Users wanting conversational fallback wait until Threadripper ships (timeline TBD) |
| **B. Mac Mini interim via litellm-gateway** | HA `conversation` integration points at `http://192.168.10.145:4000/v1/chat/completions` with model `qwen2.5-coder:7b` (or a smaller general-purpose model added for this purpose, e.g., `qwen2.5:7b-instruct`). | • Conversational fallback available immediately • Reuses existing litellm-gateway → Vault credential pattern • Easy to disable later by removing the HA conversation integration entry | • Adds Mac Mini load during HA assist queries (modest: 7B model inference is sub-second after warm-up) • Couples HA voice UX to Mac Mini availability • Violates "Mac Mini = control plane only" if interpreted strictly |
| **C. Hybrid** | Default voice routes use HA built-in NLU (no LLM). A user-explicit wake phrase ("Hey Jarvis, ask AI ...") triggers the Mac Mini litellm fallback. | • LLM fallback exists but is opt-in per query • Mac Mini load gated to explicit asks (low frequency) • Easy to retire once Threadripper online (just remove the wake-phrase trigger) | • Slightly more complex Phase 4 wiring (two pipelines configured) • User has to remember the trigger phrase |

**Operator recommendation**: **Option C (hybrid)**. Lowest commitment, lowest Mac Mini load, escape hatch is one config-entry deletion.

**Scoping note**: Block 3 P3 creates the Wyoming pipeline. P3.9 is the single config entry where this decision lands. Awaiting user choice.

---

## §A.8 — Other concerns surfaced during audit

1. **HA OS 17.1 → 17.2 update available**, **Core 2026.4.1 → 2026.4.4 update available**, **Supervisor 2026.04.0 → not auto-checked here**. Phase 2 P2.1 (HA wipe + reinstall) should pull the latest stable from the channel rather than restoring from current snapshot — this gets versions current automatically.

2. **`8b8632af_meross_local_broker` (Meross integration)** is currently `started`. After wipe, the Meross integration would need this broker re-running before pairing. Add-on snapshot would preserve it; alternatively a fresh install via the Meross 3rd-party repo (already in `/store`).

3. **`cb646a50_get` add-on (1.3.1, stopped)** is a HACS supplement. HACS itself is *not* a HA core add-on — it's a custom_components install. Inventory shows HACS state via WS `hacs/*` was queried successfully; HACS will need re-bootstrap after wipe (manual step, ~5 min).

4. **`NetworkManager-wait-online.service` is in `failed` state** on the HA host (per `/host/services`). This is benign at runtime (HA OS works fine without it) but is the kind of latent-failure entry that could mask future network-bring-up issues. Out of Block 3 scope, but flagged.

5. **0 ESPHome devices, 0 Wyoming devices, 0 ZHA/Z2M deployments** — confirmed via inventory + WS device_registry probe. Phase 4 wake-word satellites are all greenfield. No migration burden.

6. **15 Areas already defined** (`Backyard, Deck, Foyer, Front Porch, Garage, Kitchen, Living Room, Master Bathroom, Master Bedroom, Master Closet, MDF, Movie Room, Office, Upstairs Hallway, Workout Area`). Phase 2 P2.4 should preserve these by re-creating area definitions from this list immediately after wipe (the area structure is small; YAML re-entry is faster than a full backup-restore).

7. **76 devices, 213 entities, 1 dashboard ("map")** in current state. The single dashboard means Phase 5 Lovelace framework starts from a clean slate — no migration anxiety.

---

## §A.9 — Pre-Phase-2 readiness checklist

| Foundation | State |
|---|---|
| HA host hardware confirmed (4 cores, 16 GB, 250 GB SSD, NUC class) | ✅ |
| HA host healthy (0 unsupported / 0 unhealthy / 0 issues) | ✅ |
| Supervisor automation reachable (WebSocket proxy with current token) | ✅ |
| Cast targets enumerated (4 reachable) | ✅ |
| Voice add-ons available in core store | ✅ |
| Wyoming ports free on .141 (10200, 10300) | ✅ |
| Mac Mini Vault unsealed | ✅ |
| Mac Mini Ollama + litellm-gateway live (for §A.7 Option B/C) | ✅ |
| Mac Mini ports for 3 CATT containers free (8124–8126 proposed) | ✅ |
| Caddy slot for `homeassistant.internal` | ⚠️ NOT PRESENT — Block 3 P2.5 adds |
| Caddy slot for `catt.internal` | ⚠️ NOT PRESENT — Block 3 P6.4 adds |
| Integration credential map | ⚠️ Vault holds none; HA wipe loses all (re-pair list above) |
| Whisper model decision (default = `small-int8`) | ⚠️ awaiting user confirmation |
| Ollama deferral decision (default recommendation = Option C hybrid) | ⚠️ awaiting user choice |
| Broken-integration disposition (Sonoff / TP-Link / Govee — drop or fix?) | ⚠️ awaiting user decision |
| HA OS / Core update during rebuild (latest channel vs snapshot) | ⚠️ awaiting user choice |

---

## Pause-and-surface gate

Phase 1 audit complete. Five surface-back items for user review (per Block 3 plan §Phase 1):

1. **HA host specs** — Intel NUC class (4 cores, 16 GB RAM, 250 GB mSATA SSD, generic-x86-64 amd64). Healthy. → §A.1
2. **Integration credential map** — **Vault stores none**; HA wipe discards all integration auth. Re-pair list documented in §A.2 (Hue, Caséta, Shelly, Cast/Nest, Mobile App at minimum; Sonoff/TP-Link/Govee disposition pending).
3. **Whisper model recommendation** — `small-int8` (244 MB, ~600 MB RAM, 1-2× real-time on 4×amd64). Fallback `base-int8`. → §A.5
4. **Ollama decision matrix** — three options framed (defer / Mac Mini interim / hybrid). Operator recommendation: **Option C hybrid** (HA built-in NLU default; "ask AI" trigger phrase routes to Mac Mini litellm-gateway). → §A.7
5. **Other concerns** — HA OS/Core updates available, NetworkManager-wait-online.service failed (benign), 15 Areas to recreate, 4 broken integrations to disposition. → §A.8

**Phase 2 (HA wipe + clean rebuild) is gated on user response to items 2, 3, 4, 5.**

**Standing rules confirmed in effect for Block 3** (carried forward from Block 2): canonical Vault Agent sidecar pattern; no `.env` files; hash-only credential verification; provision via shell, not browser; foundation-first; batch credential decisions; autonomous non-blocking fixes; surface only real blockers.

---

**Audit complete. Standing by for user decisions.**
