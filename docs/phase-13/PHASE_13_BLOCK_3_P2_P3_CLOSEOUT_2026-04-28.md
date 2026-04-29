# Phase 13 Block 3 — P2.4 close + P3 deliverable

**Date**: 2026-04-28
**Operator**: claude-opus-4-7[1m]
**Scope**: P2.4 batch resolution (D1, D4 done; D2/D3 deferred) + Phase 3 local voice infrastructure (P3.1–P3.7)

This document supersedes/extends `PHASE_13_BLOCK_3_P2_RESULTS_2026-04-28.md` for everything decided after the P2.4 batch directive.

---

## P2.4 batch resolution status

| Decision | Verdict | Action this session | Verified state |
|---|---|---|---|
| **D1**: drop `albertogeniola/meross-homeassistant` (cloud), keep `krahabb/meross_lan` (LAN) | APPROVED | Confirmed already removed (no entry in `hacs/repositories/list` with `installed=true`) | HACS installed = 3: `hacs/integration`, `ha-warmup/warmup`, `krahabb/meross_lan` |
| **D2**: Meross credentials | PENDING — project manager | Vault path `secret/homeassistant/integrations/meross_lan` reserved (empty); `meross_lan` config_entry not yet created | 0 entries with domain=`meross_lan` |
| **D3**: Warmup credentials | PENDING — project manager | Vault path `secret/homeassistant/integrations/warmup` reserved (empty); `warmup` config_entry not yet created | 0 entries with domain=`warmup` |
| **D4**: drop `file_editor` add-on | DROP | Confirmed already uninstalled (no `core_configurator` in `/addons` list) | 6 add-ons installed: `core_matter_server`, `a0d7b954_vscode`, `core_ssh`, `core_whisper`, `core_piper`, `core_openwakeword` |

**P2.4 closes** with D1 + D4 done. D2 + D3 remain blocked on user-supplied credentials and are surfaced for the project manager to resolve via standard credential-prompt flow. The two integrations show in the KEEP-list count as "0 paired, awaiting credential" — operationally non-blocking for the rest of Block 3.

---

## P3 — Local voice infrastructure

### Add-ons installed & started

| Slug | Version | Started | Memory @ idle | Notes |
|---|---|---|---|---|
| `core_whisper` | 3.1.0 | yes | 488 MB | model=small-int8 (D3) — 488 MB RAM = small-int8 model in memory; ~250 MB downloaded over network on first boot |
| `core_piper` | 2.2.2 | yes | 40 MB | voice=en_US-lessac-medium (Piper default) |
| `core_openwakeword` | 2.1.0 | yes | 31 MB | bundled wake words: okay_nabu, hey_jarvis, hey_mycroft, alexa, hey_rhasspy |

Wyoming protocol ports (internal docker network only — `172.30.33.0/24`): 10300 (Whisper), 10200 (Piper), 10400 (OpenWakeWord). Not exposed on the LAN; HA reaches them via supervisor-internal hostnames `core-whisper`, `core-piper`, `core-openwakeword`.

### Whisper configuration (D3 — small-int8)

```yaml
model: small-int8
stt_library: faster-whisper
custom_model_type: faster-whisper
language: en
beam_size: 1
debug_logging: false
```

`beam_size: 1` chosen for fastest single-pass decoding (small-int8 is already a low-latency model; higher beams add latency without quality gain on en-US speech).

### Wyoming integration (HA-side config_entries)

Created via REST `POST /api/config/config_entries/flow` with `handler: wyoming`, then submitted `{host, port}` for each:

| Title | host | port | entry_id | state |
|---|---|---|---|---|
| `faster-whisper` | core-whisper | 10300 | `01KQBKFZVEMFZTNGZCQKFN9N8R` | loaded |
| `piper` | core-piper | 10200 | `01KQBKFZYFF4CPTKE8XFCM831D` | loaded |
| `openwakeword` | core-openwakeword | 10400 | `01KQBKG01VYNM8D18B641FTNPQ` | loaded |

Pre-existing supervisor discoveries (`/discovery`) all four resolved: `matter`, `wyoming/core_whisper`, `wyoming/core_piper`, `wyoming/core_openwakeword`.

### Voice Assist pipeline

The pre-existing pipelines (`Home Assistant`, `Home Assistant Cloud`) referenced deleted cloud STT/TTS engines after the wipe. Cleaned up:

- Renamed `Home Assistant` → `Home Assistant (Local Voice)`, repointed engines:
  - `conversation_engine = conversation.home_assistant` (HA NLU)
  - `stt_engine = stt.faster_whisper` / `stt_language = en`
  - `tts_engine = tts.piper` / `tts_language = en_US` / `tts_voice = en_US-lessac-medium`
  - `wake_word_entity = wake_word.openwakeword` / `wake_word_id = okay_nabu`
- Set as `preferred_pipeline`
- Deleted orphan `Home Assistant Cloud` pipeline

### End-to-end NLU smoke test

`POST conversation/process` via WebSocket:

| Input | response_type | speech |
|---|---|---|
| "what is the time" | `action_done` | "11:13 PM" |
| "turn on the kitchen light" | `action_done` | "Turned on the lights" |

NLU pipeline confirmed functional. STT/TTS audio path testing deferred to Phase 4 satellite work (requires a Wyoming voice satellite or equivalent to source audio).

### D4 (Option C hybrid Ollama "ask AI" trigger) — DEFERRED

Currently `conversation.home_assistant` (NLU) is the only conversation agent. The "ask AI" trigger phrase routing → `litellm-gateway`/Ollama is an additive enhancement and is **deferred to Phase 4** (when satellite testing creates demand) rather than wired blind in Phase 3. Pre-condition decision the project manager will need then: whether HA's `ollama` integration points at:

- (a) Mac Mini Ollama direct: `http://192.168.10.145:11434` — simplest, bypasses the gateway
- (b) `litellm-gateway` via Caddy: `https://litellm.internal` — requires Caddy CA trust on HA OS, plus DNS, plus the Ollama-format compatibility check

Recommendation when surfaced: option (a) for now. Move to (b) only when the gateway adds value (multi-model routing, auth, observability).

---

## Voice infrastructure — Phase 3 deliverable status

| Sub-deliverable | Status |
|---|---|
| P3.1 install Whisper add-on | ✓ |
| P3.2 install Piper add-on | ✓ |
| P3.3 install openWakeWord add-on | ✓ |
| P3.4 configure Whisper small-int8 + start | ✓ |
| P3.5 verify STT/TTS/wake_word entities exist | ✓ |
| P3.6 configure Voice Assist pipeline (NLU + local engines) | ✓ |
| P3.7 NLU end-to-end smoke test | ✓ |
| P3.8 Ollama "ask AI" trigger (D4 Option C hybrid) | deferred to Phase 4 |
| P3.9 STT audio path test | deferred to Phase 4 (no satellite mic) |

P3 closes with all functional infrastructure in place. The two deferred items both depend on Phase 4 satellite work.

---

## New lessons learned

### 1. Vault KV-v2 field name `token`, not `api_key`

`PHASE_13_BLOCK_3_P2_RESULTS_2026-04-28.md` table 2 ("Vault state") labeled the HA-token field as `api_key`. Actual field at `secret/homeassistant/api` is `token`. A second field `homepage_token` mirrors the same value (sha256-12 = `cda3bb49b25f`, len 183). Both fields hash identically — they hold the same long-lived bearer.

### 2. Supervisor REST `success: false` is frequently a false negative on HA OS 17.2

`/addons/<slug>/restart`, `/addons/<slug>/start`, and similar lifecycle endpoints regularly return `{"success": false, "error": {"code": "unknown_error", "message": ""}}` *while the operation succeeds*. Three observed instances this session: (a) initial install of `core_whisper` (`message: "App core_whisper is already installed"` — install actually succeeded), (b) `core_whisper/start` returned false despite transitioning to `state=started`, (c) `core_whisper/restart` returned false despite transitioning through `startup` → `started` with the new `model=small-int8` loaded.

**Doctrine**: do not trust the `success` field on supervisor lifecycle calls. Verify by polling `/addons/<slug>/info` for `state == "started"` and `options.<field>` matching the intended config.

### 3. HA OS 17.2 supervisor-info "stub" fields — refined

The earlier P2 results doc said: "some `data` fields return `None` in HA OS 17.2; use service calls on `update.*` entities to drive add-on updates instead". More precise lesson: the `installed`, `state`, `version`, `boot`, `options`, `network`, `ip_address`, `hostname` fields *do* populate correctly — they just stay None until the add-on has been started for the first time. The 5-minute install-poll loop showing `installed=None state=unknown` was correct: those add-ons were installed but had not yet been started. Once started, all info fields populate.

### 4. WebSocket lacks `config_entries/flow/init`

Trying `config_entries/flow/init` over WebSocket returns `{"code": "unknown_command"}`. To start a config flow programmatically, use REST: `POST /api/config/config_entries/flow {"handler": "<integration>"}` returns a flow_id and schema; `POST /api/config/config_entries/flow/<flow_id> <user_input>` advances the flow. WebSocket is for listing/managing already-created entries.

### 5. Wyoming entity attributes — `state=unknown` and `supported_languages=[]` is normal

STT/TTS/wake-word entities created via Wyoming integration keep `state=unknown` until first runtime use. STT entities also report `supported_languages=[]` because Wyoming engines constrain language at the engine level (the add-on's `language: en` option), not via HA-discovered metadata. Verify the engine is actually loaded by checking `/addons/<slug>/stats` for nonzero memory_usage and a network_rx that matches the model size.

### 6. OpenWakeWord bundled wake words

Default model bundle: `okay_nabu` (note: with `y`, not `ok_nabu`), `hey_jarvis`, `hey_mycroft`, `alexa`, `hey_rhasspy`. The pipeline-level `wake_word_id` field accepts any of these. Initial setting of `ok_nabu` was accepted by the pipeline-update API silently — a wake word that never matches. Always pull `wake_word/info` first and use a value present in the returned `wake_words[*].id` list.

---

## Outstanding items rolled forward

1. **D2 Meross credentials** — pending project manager
2. **D3 Warmup credentials** — pending project manager
3. **D4 Ollama "ask AI" trigger** — pending Phase 4 satellite testing
4. **Bearer-token-via-Caddy 401** — pending Phase 14 Caddy/HA work (workaround: scripts use direct LAN `192.168.10.141:8123`)
5. **STT audio path test** — pending Phase 4 voice satellite
