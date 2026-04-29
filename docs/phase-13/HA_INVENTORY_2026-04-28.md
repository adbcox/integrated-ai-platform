# Home Assistant Inventory — Block 3 (Display & Voice Layer) Planning Probe

**Probe date**: 2026-04-28
**Target**: Home Assistant Core at `http://192.168.10.141:8123` (note: HTTP not HTTPS — TLS not configured on the HA host)
**Operator**: claude-opus-4-7[1m] read-only probe; no mutations
**Auth**: long-lived access token from `secret/homeassistant/api` (Vault), scope: API + WebSocket; **does not include supervisor scope**

---

## 1. System Overview

| Field | Value |
|---|---|
| HA version | **2026.4.1** |
| Components loaded | 236 |
| Time zone | America/New_York |
| Country / language | US / en |
| Currency | USD |
| Unit system | Imperial (°F, mph, gal, ft², psi, lb, mi, in) |
| External / internal URL | not set |
| Config dir | `/config` |
| Bluetooth | enabled (Intel Corporate adapter) |
| Backup integration | loaded |

---

## 2. Add-ons (inferred — supervisor API blocked)

**Limitation**: `/api/hassio/addons` returned empty body and `/api/hassio/info` returned `401`. The long-lived token does not carry supervisor scope, so direct add-on enumeration is not possible. Add-on presence is **inferred** from registered integrations and components.

### Confirmed present (via supervisor config_entry)

- **Supervisor itself**: `hassio` config_entry loaded (Title: Supervisor) — therefore HAOS / Supervised installation, not Container.

### Block-3-spec add-ons — present/absent inference

| Add-on | Detected? | Evidence |
|---|---|---|
| ESPHome | ❌ absent | no `esphome` config_entry, no `esphome.*` components |
| Whisper (Wyoming STT) | ❌ absent | no `wyoming` config_entry; STT engines limited to `stt.home_assistant_cloud` |
| Piper (Wyoming TTS) | ❌ absent | TTS engines limited to `tts.home_assistant_cloud` + `tts.google_translate_en_com` |
| OpenWakeWord | ❌ absent | no `wake_word` engines registered (component loaded but unused) |
| Mosquitto MQTT | ❌ absent | no `mqtt` config_entry, no `mqtt.*` components |
| File Editor / Studio Code | unknown | no API surface; cannot infer |
| Samba | unknown | no API surface; cannot infer |

### Other capabilities present

- **HACS** (Home Assistant Community Store): installed and loaded (`hacs` config_entry, `hacs.update`, `hacs.switch` components).
- **go2rtc**: loaded (camera streaming relay).
- **Cloud (Nabu Casa)**: subscription active — Cloud STT, Cloud TTS, Cloud Voice Assistant pipeline configured.
- **HA Connect ZBT-1 (SkyConnect)**: Zigbee + Thread/Matter coordinator (`homeassistant_sky_connect` + `zha` + `thread` + `matter` config_entries).

---

## 3. Integrations (config_entries, total = 28)

### Top integrations by entry count

| Domain | Count | State | Notes |
|---|---|---|---|
| `tplink` | 6 | **setup_error** | Kasa lights/plugs offline or auth failure |
| `hassio` | 1 | loaded | Supervisor |
| `hue` | 1 | loaded | Hue Bridge ecb5faaf77b6 |
| `lutron_caseta` | 1 | loaded | bridge 032257f4 |
| `zha` | 1 | loaded | via SkyConnect ZBT-1 |
| `cast` | 1 | loaded | Google Cast |
| `matter` | 1 | loaded | |
| `thread` | 1 | loaded | |
| `bluetooth` | 1 | loaded | |
| `sonoff` | 1 | **not_loaded** | adbcox@gmail.com — needs re-auth |
| `govee_light_local` | 1 | **setup_retry** | discovery flapping |
| `shelly` | 1 | loaded | shellyplusrgbwpm-d8132add2154 |
| `mobile_app` | 1 | loaded | "Adrian" |
| `cloud` | 1 | loaded | Home Assistant Cloud |
| `hacs` | 1 | loaded | |
| `go2rtc` | 1 | loaded | |
| `backup` | 1 | loaded | |
| `met` / `sun` / `radio_browser` / `google_translate` / `shopping_list` | 1 each | loaded | |

### Block-3 integrations lookup

| Wanted | Status |
|---|---|
| `cast` (Google Cast) | ✅ loaded |
| `matter` | ✅ loaded |
| `thread` | ✅ loaded |
| `zha` | ✅ loaded |
| `mobile_app` | ✅ loaded |
| `hacs` | ✅ loaded |
| `cloud` | ✅ loaded |
| `bluetooth` | ✅ loaded |
| `go2rtc` | ✅ loaded |
| `lutron_caseta` / `hue` / `shelly` / `sonoff` / `tplink` / `govee_light_local` | ✅ loaded (with caveats noted above) |
| `plex` | ❌ absent |
| `sonarr` / `radarr` | ❌ absent |
| `calendar` | ❌ absent (no `calendar` integration; Nextcloud CalDAV not yet wired into HA) |
| `ollama` | ❌ absent (no local-LLM conversation agent) |
| `mqtt` | ❌ absent |
| `esphome` | ❌ absent |
| `wyoming` | ❌ absent |
| `assist_pipeline` (loaded as core component, but no add-on engines) | ⚠️ partial |
| `openwakeword` / `piper` / `whisper` | ❌ absent |
| `homekit` | ❌ absent |
| `google_assistant` | ❌ absent |
| `alexa` | ❌ absent |

---

## 4. Entity Inventory

| Domain | Count |
|---|---|
| `sensor` | 58 |
| `update` | 23 |
| `light` | 22 |
| `switch` | 22 |
| `number` | 17 |
| `button` | 13 |
| `binary_sensor` | 12 |
| **`media_player`** | **10** |
| `event` | 9 |
| `automation` | 8 |
| `select` | 6 |
| `scene` | 5 |
| `tts` | 2 |
| `conversation`, `stt`, `zone`, `person`, `sun`, `device_tracker`, `todo`, `weather` | 1 each |
| `assist_satellite`, `wake_word` | **0** |

**Total entities**: ~213

### Cast targets (`media_player.*`)

| Entity | State | Friendly name |
|---|---|---|
| `media_player.master_bedroom_display` | off | Master Bedroom Display |
| `media_player.kitchen_speaker` | off | Kitchen speaker |
| `media_player.kitchen_display` | off | Kitchen Display |
| `media_player.shield_2` | off | SHIELD |
| `media_player.shield`, `.shield_3`, `.shield_4`, `.shield_5` | unavailable | (duplicate-seeming entries — likely stale Cast discovery) |
| `media_player.chromecast` | unavailable | |
| `media_player.projector` | unavailable | |

5 of 10 media_players are reachable; the rest are stale Cast discovery from previous sessions and warrant cleanup before Block 3 dashboards anchor on them.

### Lights / switches

- 22 lights: Hue (Foyer, Pendant, Kitchen Cabinet, Kitchen Main, Upstairs Hallway dimmers), TP-Link Kasa (KS225, ES20M), Sonoff variants. Many `unavailable` due to TP-Link Kasa setup_error.
- 22 switches: mostly Sonoff/TP-Link auxiliary "Auto update / LED" pseudo-switches plus a few real plugs. Real-world controllable count is probably <8 once auxiliary switches are filtered.

### Binary sensors by class

| device_class | Count |
|---|---|
| connectivity | 7 |
| motion | **2** |
| opening | 2 |
| (none) | 1 |

Only **2 motion sensors** for presence-driven dashboards. Block 3 will need additional sensors or we accept time-based / occupancy-by-other-signal dashboards.

---

## 5. Device Registry (76 devices)

### By manufacturer

| Manufacturer | Devices |
|---|---|
| TP-Link | 8 |
| Signify (Hue) | 7 |
| Home Assistant (HA-internal) | 5 |
| NVIDIA (Shield) | 5 |
| eWeLink (Sonoff) | 5 |
| Google Inc. | 4 |
| SONOFF | 4 |
| Philips | 4 |
| Lutron | 3 |
| coolkit / `_TZ3000_hhiodade` (Zigbee generics) | 3 each |
| ORVIBO | 3 |
| Apple, Govee, Shelly, Met.no, Intel, others | 1–2 |
| **HACS-related** (Community Apps / Store / hacs.xyz / Meross addon / krahabb / albertogeniola / AlexxIT / ha-warmup / Inspur / Nabu Casa / Official apps) | 1 each |

### ESPHome / Wyoming devices

- **ESPHome devices**: 0
- **Wyoming devices**: 0

---

## 6. Lovelace / Dashboards

| Item | Value |
|---|---|
| Dashboards (storage-mode) | **1** — `map` (title: Map) |
| Default dashboard `views` | 0 (likely YAML-mode default OR auto-generated UI; storage API returned empty) |
| Custom Lovelace resources | **0** (no Mushroom, no layout-card, no button-card, no mini-graph-card, etc.) |

This is essentially a **greenfield UI surface** for Block 3. HACS is installed, so HACS-mediated frontend resource installation is the path. Currently no operator-facing dashboard exists beyond the map view — Block 3 will be additive, not retrofitting an existing UI.

---

## 7. Voice / Assist Current State

### Pipelines

| Name | STT | TTS | Conversation agent |
|---|---|---|---|
| Home Assistant | (none) | `tts.home_assistant_cloud` | `conversation.home_assistant` |
| **Home Assistant Cloud** (preferred) | `stt.home_assistant_cloud` | `tts.home_assistant_cloud` | `conversation.home_assistant` |

`preferred_pipeline = 01jb0a4getd440yyp0crm703d2` (the Cloud pipeline).

### Engines registered

- **STT providers**: `stt.home_assistant_cloud` (only).
- **TTS providers**: `stt.home_assistant_cloud`, `tts.google_translate_en_com`.
- **Wake word providers**: 0 registered (component `wake_word` loaded but no engines exposed).
- **Conversation agents**: 1 (`conversation.home_assistant` — built-in intent-matching, **no LLM-backed agent**).

### Implication for Block 3

Voice currently runs via **Nabu Casa Cloud subscription** — fine as a baseline but not aligned with the platform's "no cloud-LLM dependency" doctrine. Block 3 will swap STT to local Whisper add-on, TTS to local Piper add-on, wake-word to local OpenWakeWord, and add an Ollama-backed conversation agent for natural-language commands.

---

## 8. HACS State

| Field | Value |
|---|---|
| HACS config_entry | ✅ present |
| `hacs.*` components loaded | `hacs`, `hacs.switch`, `hacs.update` |
| Custom Lovelace resources installed | **0** (HACS is installed but no frontend resources have been added through it yet) |
| Custom integrations installed | unknown (HACS REST API not enumerated by token; would need HACS-specific WebSocket calls or settings page introspection) |

**Limitation**: detailed HACS inventory (which custom integrations + frontend repos are configured) was not pulled. Standard HACS REST endpoints (`/api/hacs/*`) returned `404`; HACS exposes its config via HA's WebSocket `hacs/*` family which was not in the probe set. Surface back to user if that detail is required for Block 3 planning.

---

## 9. Block 3 Gap Analysis

### Display layer (operator/family wall-mounted dashboard)

| Block 3 spec item | Current state | Gap |
|---|---|---|
| Wall-mounted display target (Cast or Fully-Kiosk) | 5 reachable Cast devices (Master Bedroom, Kitchen, Shield-2) | Sufficient targets, but no dashboard cast automation yet |
| Operator dashboard (Lovelace YAML) | 0 views in default dashboard | greenfield — design from scratch |
| Custom cards (Mushroom, layout, button, etc.) | 0 resources installed | install via HACS in Block 3 |
| Zone/area mapping | not enumerated in this probe (area_registry not pulled) | re-probe if area-driven views needed |
| Stale Cast targets (5 unavailable shields/projectors) | clutter | clean up before binding dashboards to media_player.* |
| TP-Link Kasa setup_error | 6 entries broken | fix or remove before lights show as "unavailable" on dashboard |

### Voice layer

| Block 3 spec item | Current state | Gap |
|---|---|---|
| Local STT (Whisper) | not installed; using Cloud | install Wyoming-Whisper add-on → wire into pipeline |
| Local TTS (Piper) | not installed; using Cloud | install Wyoming-Piper add-on → wire into pipeline |
| Wake word (OpenWakeWord) | component loaded, 0 engines | install OpenWakeWord add-on |
| Voice satellite hardware | 0 ESPHome devices, 0 Wyoming satellites | provision satellite (ESPHome firmware on M5/voice PE or ESP32-S3) |
| LLM conversation agent | only built-in intent matcher | add `ollama` integration pointing to platform Ollama (LiteLLM proxy or direct) for natural-language fallback |
| Pipeline preference | Cloud preferred | swap to local-engine pipeline once add-ons in place |

### Supporting integrations

| Block 3 spec item | Current state | Gap |
|---|---|---|
| MQTT broker | absent | install Mosquitto add-on; useful for ESPHome / future devices |
| Calendar (CalDAV from Nextcloud) | absent | add `caldav` integration pointing to `nextcloud.internal` (4 calendars exist on platform) |
| Plex | absent | add `plex` integration if Plex queries are part of voice scope |
| Sonarr/Radarr | absent | optional; only if media-mgmt dashboards in scope |
| Ollama integration | absent | add `ollama` integration → platform Ollama on Mac Mini |

---

## 10. Limitations Encountered

| Limitation | Workaround used | Should the user re-issue a token? |
|---|---|---|
| `/api/hassio/addons` empty + `/api/hassio/info` 401 — long-lived token lacks supervisor scope | inferred add-on absence from missing config_entries | **Optional**: a supervisor-scope token would let Block 3 planning enumerate exact add-on versions before installing more. Not a blocker — install-then-verify works as a fallback. |
| `/api/hacs/*` returns 404 | HACS exposes via WebSocket; this probe didn't query it | Re-probe via WS `hacs/...` if installed-customizations list matters before Block 3 |
| `/api/lovelace/config` returned 404 (REST); used WS `lovelace/config` instead | resolved | n/a |
| HA exposed over plain HTTP (port 8123, no TLS) | acceptable for LAN; flag for Block 3 to consider Caddy reverse-proxy `homeassistant.internal` site if .internal-name parity matters | not blocking |
| `tplink` has 6 setup_errors; `sonoff` not_loaded; `govee_light_local` setup_retry | flagged for cleanup as Block-3 prerequisite | not blocking |

---

## 11. Summary

**Present (Block-3 ready)**

- HA 2026.4.1 reachable on `http://192.168.10.141:8123`, API token valid, WebSocket auth working.
- 236 components, 28 integrations, 76 devices, ~213 entities.
- HAOS / Supervised install (Supervisor present), HACS installed.
- SkyConnect ZBT-1 → Zigbee (`zha`) + Thread + Matter all loaded.
- Voice pipelines defined (Cloud-backed); cast targets enumerable; mobile-app provisioned.

**Gaps to fill in Block 3**

- **Add-ons to install**: Mosquitto MQTT, ESPHome, Wyoming-Whisper, Wyoming-Piper, OpenWakeWord (likely 5 add-ons).
- **Integrations to add**: `mqtt`, `esphome`, `wyoming`, `ollama`, `caldav` (Nextcloud), `plex` (optional).
- **Lovelace work is greenfield**: 0 custom resources, 0 default views — Block 3 designs from a blank canvas. Plan to install Mushroom + layout-card + button-card via HACS.
- **Voice satellite hardware**: 0 ESPHome / 0 Wyoming devices; needs physical satellite provisioning (ESP32-S3 / Voice-PE).
- **Pre-Block-3 hygiene**: fix `tplink` setup_error, re-auth `sonoff`, remove 5 stale Cast media_players.
- **Move voice off Cloud**: swap pipeline to local engines once add-ons land; replace built-in intent matcher with Ollama-backed `conversation` agent for natural-language fallback.

**Access limitations**

- Supervisor add-on enumeration blocked by token scope (supervisor scope not granted to long-lived token). Workable around by installing-then-verifying via integration registration.
- HACS detailed inventory not pulled in this probe (would require WebSocket `hacs/*` calls).

---

**This document is the planning baseline for Block 3 (Display & Voice Layer). All facts above are anchored to a single read-only API/WebSocket pull executed 2026-04-28 from the Mac Mini control plane.**
