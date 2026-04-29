# Phase 13 Block 3 P4 — Voice Satellite Framework

**Date**: 2026-04-29
**Operator**: claude-opus-4-7[1m]
**Scope boundary**: framework only (templates, workflow, room→satellite mapping). Physical satellite deployment is **device-population work**, out of Block 3.

---

## Deliverables (this phase)

| File | Purpose |
|---|---|
| `config/phase-13/voice-satellite/satellite-template.yaml` | ESPHome YAML template — the canonical specification for what a wake-word satellite is on this platform |
| (this doc) | Deployment workflow + per-room mapping |

No HA-host changes. No add-on installs. No physical-device commits.

---

## Hardware specification

**Recommended baseline**: M5Stack Atom Echo (~USD 13/unit).

- ESP32 + 4 MB flash + PDM mic (SPM1423) + 1 W speaker
- Single GPIO27 NeoPixel for pipeline-state visualization
- USB-C powered, fits a 3D-printable wall plate

**Acceptable alternatives**:

- ESP32-S3 dev board + INMP441 PDM mic + MAX98357A I2S amp (≈ USD 10 in parts)
- ESP32-S3-Box (with display + UI feedback) for high-traffic rooms

**Not recommended**:

- Generic "smart-speaker conversion" boards using analog mics — noise-suppression unreliable
- Any board lacking a hardware reset button — recovery from a bad OTA becomes painful

---

## Per-room mapping

The 15 areas from §A.8 of the foundation audit (`PRE_BLOCK_3_FOUNDATION_AUDIT_2026-04-28.md`) are the canonical satellite slots. The following is the recommended initial fleet — **NOT a deployment commit**; populated per-block when devices arrive:

| Area | Hostname | Friendly name | Priority |
|---|---|---|---|
| Kitchen | `kitchen` | "Kitchen Voice Satellite" | 1 — daily-driver area |
| Living Room | `living-room` | "Living Room Voice Satellite" | 1 |
| Master Bedroom | `master-bedroom` | "Master Bedroom Voice Satellite" | 2 |
| Office | `office` | "Office Voice Satellite" | 2 |
| Movie Room | `movie-room` | "Movie Room Voice Satellite" | 3 |
| Workout Area | `workout-area` | "Workout Voice Satellite" | 3 |
| Master Bathroom | `master-bathroom` | "Master Bathroom Voice Satellite" | 4 |
| Garage | `garage` | "Garage Voice Satellite" | 4 |
| Backyard | `backyard` | "Backyard Voice Satellite" | 5 — outdoor |
| Deck | `deck` | "Deck Voice Satellite" | 5 — outdoor |
| Front Porch | `front-porch` | "Front Porch Voice Satellite" | 5 — outdoor |
| Foyer | `foyer` | "Foyer Voice Satellite" | n/a — pass-through area, defer |
| Master Closet | `master-closet` | "Master Closet Voice Satellite" | n/a — defer |
| MDF | `mdf` | "MDF Voice Satellite" | n/a — utility, defer |
| Upstairs Hallway | `upstairs-hallway` | "Upstairs Hallway Voice Satellite" | n/a — pass-through, defer |

Outdoor satellites need weather-proofing — they are scope-flagged for a later block.

---

## Deployment workflow (when devices arrive — out of scope this block)

For posterity / future operator. **Do not execute as part of this Phase 4 close.**

1. Install ESPHome add-on on the HA host:
   `Settings → Add-ons → Add-on Store → ESPHome → Install + Start`.
   The 3rd-party repo `https://github.com/esphome/home-assistant-addon` is the canonical source.

2. Populate `/config/esphome/secrets.yaml` on the HA host with `wifi_ssid` + `wifi_password`. This file is **HA-host-only** and is not checked into this repo (Wi-Fi credentials live in Vault as `secret/wifi/home`).

3. Per satellite:
   - Copy the template: `cp satellite-template.yaml <hostname>.yaml`
   - Replace the two `__SUBSTITUTE_*__` tokens
   - Generate a per-device `api.encryption.key` (32-byte base64) and `ota.password` (any 32-char random string). Store both in Vault at `secret/voice-satellites/<hostname>` as fields `api_key`, `ota_password`. Replace the `__GENERATE_*__` tokens.
   - Compile + flash via the ESPHome add-on web UI: USB initial flash, OTA thereafter
   - Boot the device. mDNS discovery → HA's ESPHome integration auto-creates a config_entry within ~30 s.
   - Assign to its Area in HA. The Voice Assist pipeline (`Home Assistant (Local Voice)`) is automatically used because it is the preferred pipeline (set during Phase 3 P3.6).

4. Smoke test (per satellite):
   - Wake-word: say "okay nabu" near the device. Status LED → blue.
   - STT: say a known intent, e.g. "what time is it". Expected response: TTS in the room's speaker.
   - Latency: wake → response < 2.5 s on a quiet network. If higher, drop the Whisper add-on model from `small-int8` to `base-int8` in HA's add-on options (D3 fallback).

---

## Out-of-scope (deferred)

- Physical procurement (15+ ESP32 boards, mics, amps, enclosures, PoE injectors if applicable)
- Per-device key generation + Vault writes
- Compile/flash work via ESPHome add-on
- Per-area assignment + first-boot smoke tests
- Outdoor weatherproofing for the Backyard/Deck/Front Porch satellites

These all fall under "device-population work" and will form the bulk of a future block.
