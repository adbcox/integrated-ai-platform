# Track 1.A: LiteLLM Smart Routing Proxy — Status Report

**Session Date:** 2026-05-09
**Branch:** feat/track-1a-litellm-routing
**Status:** IN PROGRESS — Stage 6 complete

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

## Stage 5 — Re-wire Goose

**Status:** ✓ COMPLETE

**Configuration Updated:** `~/.config/goose/config.yaml`

**Changes:**
- GOOSE_PROVIDER: ollama (unchanged — LiteLLM accepts Ollama-style API)
- GOOSE_MODEL: changed from `qwen2.5-coder:7b` → `qwen3-coder-30b`
- OLLAMA_HOST: changed from `http://127.0.0.1:11434` → `http://localhost:4000` (LiteLLM proxy)

**Authentication Note:** LiteLLM master_key is disabled (set to null) in proxy config to allow Ollama-style requests without authentication headers. Goose's Ollama provider does not support Bearer token auth. This is acceptable for local-only setup.

**Verification:** Goose successfully executed a test task through the LiteLLM proxy and returned the expected response.

**Routing Behavior:** Goose now routes all requests through LiteLLM proxy, with automatic fallback to local Ollama if Mac Studio LAN is unreachable.

## Stage 6 — Re-wire Aider

**Status:** ✓ COMPLETE

**Configuration Created:** `~/local-ai-workstation/configs/aider/.aider.conf.yml`
**Symlink:** `~/.aider.conf.yml` → `~/local-ai-workstation/configs/aider/.aider.conf.yml`

**Configuration Contents:**
```yaml
openai-api-base: http://localhost:4000/v1
openai-api-key: sk-local-only-not-secret
model: openai/qwen3-coder-30b
weak-model: openai/qwen2.5-coder
no-auto-commits: false
edit-format: diff
```

**Changes:**
- Aider now routes through LiteLLM proxy at localhost:4000/v1
- Primary model: qwen3-coder-30b (Mac Studio via proxy, with local fallback)
- Weak model: qwen2.5-coder (local Ollama via proxy)

**Verification:** Config file is properly formatted YAML and symlinked for automatic discovery by Aider

**Routing Behavior:** Aider will use OpenAI-compatible API through LiteLLM proxy; requests to qwen3-coder-30b will fall back to local qwen2.5-coder if Mac Studio LAN is unreachable.

## Remaining Stages

- Stage 7: [PENDING] Verify Cline + Continue
- Stage 8: [PENDING] Final status documentation
