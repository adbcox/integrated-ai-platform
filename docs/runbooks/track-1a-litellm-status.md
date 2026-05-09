# Track 1.A: LiteLLM Smart Routing Proxy — Status Report

**Session Date:** 2026-05-09
**Branch:** feat/track-1a-litellm-routing
**Status:** IN PROGRESS — Stage 4 complete

## Stage 1 — LiteLLM Proxy Installation

**Status:** ✓ COMPLETE

**Installation Method:** Official docs (https://docs.litellm.ai/) recommend `uv tool install 'litellm[proxy]'`

**Command Executed:**
```bash
uv tool install 'litellm[proxy]'
```

**Verification:**
- Installation path: `/Users/adriancox/.local/bin/litellm`
- Version: 1.83.14
- Executables installed: `litellm`, `litellm-proxy`
- `litellm --help` confirms `--config` and `--port` options available
- Version output is parseable: `LiteLLM: Current Version = 1.83.14`

## Stage 2 — LiteLLM Proxy Configuration

**Status:** ✓ COMPLETE

**Configuration File:** `~/local-ai-workstation/configs/litellm/config.yaml`

**Models Configured:**
1. `qwen2.5-coder` — Local MacBook Ollama (127.0.0.1:11434) — always available
2. `qwen3-coder-30b` — Mac Studio LAN (192.168.10.142:11434) — home network only
3. `qwen3-coder-30b-tailscale` — Mac Studio via Tailscale (commented out, operator to provide hostname)

**Router Configuration:**
- Strategy: simple-shuffle
- Retries: 2
- Timeout: 30 seconds
- Fallback chain: qwen3-coder-30b → qwen2.5-coder (if LAN unreachable, falls back to local)

**Verification:** Config syntax verified by starting proxy briefly; health check responded.

## Stage 3 — LiteLLM as launchd Service

**Status:** ✓ COMPLETE

**launchd Configuration:**
- Label: `com.adriancox.litellm`
- Plist location: `~/Library/LaunchAgents/com.adriancox.litellm.plist`
- Command: `/Users/adriancox/.local/bin/litellm --config ~/local-ai-workstation/configs/litellm/config.yaml --port 4000`
- RunAtLoad: true
- KeepAlive: true
- Logs: `~/local-ai-workstation/logs/litellm.{out,err}`

**Service Status:** Loaded and running

**Verification Tests:**

1. **Model List Endpoint:**
   ```bash
   curl -H "Authorization: Bearer sk-local-only-not-secret" \
     http://localhost:4000/v1/models
   ```
   ✓ Returns: `qwen2.5-coder`, `qwen3-coder-30b`

2. **Local Model Chat Completion (qwen2.5-coder):**
   ✓ Request succeeded; model responded with "WORKING"
   ✓ Used local Ollama (127.0.0.1:11434)

3. **Fallback Chain Test (qwen3-coder-30b → qwen2.5-coder):**
   ✓ Requested qwen3-coder-30b (configured for LAN endpoint 192.168.10.142:11434)
   ✓ LAN endpoint unreachable (off-network), router fell back to qwen2.5-coder
   ✓ Response received with "FALLBACK_OK"
   ✓ Proves: fallback chain working; router handles offline scenario automatically

**Behavioral Note:** When Mac Studio is off-network or unreachable:
- Requests to qwen3-coder-30b automatically degrade to qwen2.5-coder
- No manual intervention needed
- Transparent to agent tools (OpenCode, Goose, Aider)

## Stage 4 — Re-wire OpenCode

**Status:** ✓ COMPLETE

**Configuration Updated:** `~/local-ai-workstation/configs/opencode/opencode.json`

**Changes:**
- Replaced `ollama_macstudio_lan` + `ollama_local_offline` providers with single `litellm_local_proxy` provider
- New provider points at: `http://localhost:4000/v1` (LiteLLM proxy)
- API key: `sk-local-only-not-secret`
- Models exposed:
  - `qwen2.5-coder` (local Ollama via proxy)
  - `qwen3-coder-30b` (Mac Studio LAN via proxy, with local fallback)
- Default model: `qwen3-coder-30b` (router handles fallback to local if LAN unreachable)

**Routing Behavior:** All requests now route through the LiteLLM proxy, which:
- Attempts qwen3-coder-30b requests on Mac Studio LAN (192.168.10.142:11434)
- Falls back to local qwen2.5-coder if LAN unreachable
- Operator can override per-session via model selector in OpenCode TUI

**Verification:** Config is valid JSON; OpenCode TUI loads with new provider and models

## Remaining Stages

- Stage 5: [PENDING] Re-wire Goose
- Stage 6: [PENDING] Re-wire Aider
- Stage 7: [PENDING] Verify Cline + Continue
- Stage 8: [PENDING] Final status documentation
